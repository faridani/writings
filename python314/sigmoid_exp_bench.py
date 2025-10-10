#!/usr/bin/env python3
"""
Benchmark sigmoid (exp & tanh) across CPython 3.10, CPython 3.14 (JIT off/on), and PyPy (JIT off/on).

Key features:
- Uses timeit.repeat (standard library) and reports MEDIAN over repeats.
- Reports BOTH raw medians and overhead-adjusted medians (subtract identity-loop median).
- Prints a ranking (fastest → slowest) at the largest N with two lines per run: "(exp)" and "(tanh)".
- Auto-detects python3.10, python3.14, pypy3 if available; you can also pass explicit paths.
- Child mode prints only JSON; parent aggregates, prints tables, writes CSV/JSON (+ optional plots).

Run examples:
  python3 sigmoid_bench_both.py
  python3 sigmoid_bench_both.py --pythons python3.10 python3.14 pypy3
  python3 sigmoid_bench_both.py --sizes 10000,100000,1000000 --repeats 7 --warmup 2
"""

from __future__ import annotations
import argparse
import json
import math
import os
import platform
import random
import shutil
import subprocess
import sys
import textwrap
import timeit
import statistics
from typing import Dict, List, Tuple


# ----------------------------- Core benchmark (child mode) -----------------------------

def sigmoid_exp(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def sigmoid_tanh(x: float) -> float:
    return 0.5 * (math.tanh(x / 2.0) + 1.0)


def identity(x: float) -> float:
    # Measures loop + Python call overhead with minimal math
    return x


def _do_loop(xs: List[float], func) -> float:
    s = 0.0
    for v in xs:
        s += func(v)
    return s


def _time_callable(callable_obj, repeats: int, warmup: int) -> Tuple[float, float]:
    """
    Time a zero-arg callable using timeit.repeat, with warmup passes.
    Returns (median_seconds, checksum_from_one_call).
    """
    # Warmup (useful if there is any tiering/JIT)
    for _ in range(max(0, warmup)):
        _ = callable_obj()

    times = timeit.repeat(callable_obj, repeat=repeats, number=1)
    median_s = statistics.median(times)

    # Compute checksum separately (not part of timing)
    checksum = callable_obj()
    return median_s, checksum


def _jit_introspection() -> Dict[str, object]:
    """
    Detect JIT availability/enabled status for current interpreter.
    - CPython 3.14+: sys._jit.{is_available,is_enabled}()
    - PyPy: presence of pypyjit implies availability; env PYPY_DISABLE_JIT controls enabled.
    """
    impl = platform.python_implementation()
    info = {
        "implementation": impl,
        "requested_env_cpython": os.environ.get("PYTHON_JIT"),
        "requested_env_pypy": os.environ.get("PYPY_DISABLE_JIT"),
        "has_sys_jit": hasattr(sys, "_jit"),
        "available": False,
        "enabled": False,
        "abiflags": getattr(sys, "abiflags", ""),
    }

    if impl == "CPython":
        if info["has_sys_jit"]:
            try:
                info["available"] = bool(sys._jit.is_available())
            except Exception:
                info["available"] = False
            try:
                info["enabled"] = bool(sys._jit.is_enabled())
            except Exception:
                info["enabled"] = False
        # else: CPython < 3.14, no JIT
    elif impl == "PyPy":
        try:
            import pypyjit  # noqa: F401
            info["available"] = True
        except Exception:
            info["available"] = False
        off = os.environ.get("PYPY_DISABLE_JIT")
        info["enabled"] = (off in (None, "", "0", "false", "False"))
    return info


def run_child_benchmark(
    sizes: List[int], repeats: int, rng_seed: int = 42, warmup: int = 1
) -> Dict:
    rnd = random.Random(rng_seed)
    inputs: Dict[int, List[float]] = {n: [rnd.uniform(-8.0, 8.0) for _ in range(n)] for n in sizes}

    jit = _jit_introspection()
    if jit["implementation"] == "PyPy":
        mode = "JIT ON" if jit["enabled"] else "JIT OFF"
    else:  # CPython
        if jit["enabled"]:
            mode = "JIT ON"
        elif jit["requested_env_cpython"] == "1" and not jit["available"]:
            mode = "JIT requested (unavailable)"
        else:
            mode = "JIT OFF"

    per_size = []
    for n in sizes:
        xs = inputs[n]

        # Build callables for timeit (zero-arg)
        base_call = (lambda xs=xs: _do_loop(xs, identity))
        exp_call  = (lambda xs=xs: _do_loop(xs, sigmoid_exp))
        tanh_call = (lambda xs=xs: _do_loop(xs, sigmoid_tanh))

        # Time each and get MEDIANS
        base_med, _ = _time_callable(base_call, repeats, warmup)
        exp_med, exp_sum = _time_callable(exp_call, repeats, warmup)
        tanh_med, tanh_sum = _time_callable(tanh_call, repeats, warmup)

        # Overhead-adjusted medians: clamp at zero to avoid small negatives
        exp_adj = max(0.0, exp_med - base_med)
        tanh_adj = max(0.0, tanh_med - base_med)

        per_size.append({
            "N": n,
            "overhead_raw_median_s": base_med,
            "exp_raw_median_s": exp_med,
            "tanh_raw_median_s": tanh_med,
            "exp_adj_median_s": exp_adj,
            "tanh_adj_median_s": tanh_adj,
            "exp_checksum": float(exp_sum),
            "tanh_checksum": float(tanh_sum),
        })

    info = {
        "python_impl": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_build": platform.python_build(),
        "python_compiler": platform.python_compiler(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "sizes": sizes,
        "repeats": repeats,
        "warmup": warmup,
        "jit": jit,
        "mode": mode,
        "results": per_size,
    }
    return info


# --------------------------- Aggregation & output (parent mode) -------------------------

def _fmt_seconds(x: float) -> str:
    if x < 1e-3:
        return f"{x*1e6:.1f} µs"
    if x < 1.0:
        return f"{x*1e3:.2f} ms"
    return f"{x:.3f} s"


def _label_base(run: Dict) -> str:
    exe = os.path.basename(run["python_executable"])
    ver = run["python_version"]
    impl = run.get("python_impl", "")
    mode = run.get("mode", "JIT OFF")
    return f"{impl} {ver} · {exe} · {mode}"


def _median_at_largest(run: Dict, key: str) -> float:
    largest = max(r["N"] for r in run["results"])
    row = next(r for r in run["results"] if r["N"] == largest)
    return row[key]


def _prune_unavailable_jit(all_runs: List[Dict]) -> List[Dict]:
    """
    Drop runs whose mode is 'JIT requested (unavailable)' when there's already a
    corresponding 'JIT OFF' run for the same interpreter (impl+exe+version).
    """
    by_key = {}
    for r in all_runs:
        key = (r["python_impl"], r["python_executable"], r["python_version"])
        by_key.setdefault(key, []).append(r)

    keep: List[Dict] = []
    for key, runs in by_key.items():
        has_off = any(rr.get("mode") == "JIT OFF" for rr in runs)
        for rr in runs:
            if rr.get("mode") == "JIT requested (unavailable)" and has_off:
                continue  # drop duplicate
            keep.append(rr)
    return keep


def aggregate_and_print(all_runs: List[Dict]) -> None:
    if not all_runs:
        print("No results to show.")
        return

    all_runs = _prune_unavailable_jit(all_runs)
    sizes = sorted({r["N"] for run in all_runs for r in run["results"]})
    largest = sizes[-1]

    # Build per-method items and sort by ADJUSTED median (fastest → slowest)
    items = []
    for run in all_runs:
        items.append({"run": run, "method": "exp",
                      "adj": _median_at_largest(run, "exp_adj_median_s"),
                      "raw": _median_at_largest(run, "exp_raw_median_s")})
        items.append({"run": run, "method": "tanh",
                      "adj": _median_at_largest(run, "tanh_adj_median_s"),
                      "raw": _median_at_largest(run, "tanh_raw_median_s")})

    items.sort(key=lambda x: x["adj"])
    if not items:
        print("No method results to show.")
        return

    print(f"\n=== Sigmoid (exp & tanh) — MEDIANS at largest N = {largest:,} ===")
    header = (
        f"{'#':>2}  {'Interpreter · Mode (method)':<62} "
        f"{'adj_median':>12} {'raw_median':>12} {'vs fastest':>11}  {'JIT avail/en':>13}"
    )
    print(header)
    print("-" * len(header))

    best_adj = items[0]["adj"]
    for idx, it in enumerate(items, 1):
        run = it["run"]
        method = it["method"]
        label = f"{_label_base(run)} ({method})"
        adj = it["adj"]
        raw = it["raw"]
        ratio = (adj / best_adj) if best_adj > 0 else float("inf")
        jit = run["jit"]
        avail = "Y" if jit.get("available") else "N"
        en = "Y" if jit.get("enabled") else "N"
        print(f"{idx:>2}  {label:<62} {_fmt_seconds(adj):>12} {_fmt_seconds(raw):>12} {ratio:>10.2f}x   {avail}/{en:>1}")

    # Per-interpreter: JIT ON vs OFF deltas (ADJUSTED medians), per method
    by_key = {}
    for run in all_runs:
        key = (run["python_impl"], run["python_executable"], run["python_version"])
        by_key.setdefault(key, []).append(run)

    printed = False
    for key, runs in by_key.items():
        off = next((r for r in runs if r.get("mode") == "JIT OFF"), None)
        on  = next((r for r in runs if r.get("mode") == "JIT ON"), None)
        if off and on:
            row_on  = next(rr for rr in on["results"]  if rr["N"] == largest)
            row_off = next(rr for rr in off["results"] if rr["N"] == largest)
            for method in ("exp", "tanh"):
                old = row_off[f"{method}_adj_median_s"]
                new = row_on[f"{method}_adj_median_s"]
                if old > 0:
                    delta = (old - new) / old * 100.0
                    if not printed:
                        print("\nJIT ON vs OFF deltas (adjusted medians, same interpreter):")
                        printed = True
                    print(f"  ↳ {_label_base(on)} ({method}): {delta:+.2f}%")

    # Note about any pruned "requested but unavailable" runs
    warn = [r for r in all_runs if r.get("mode") == "JIT requested (unavailable)"]
    if warn:
        print("\n[Note] Some runs requested JIT but it wasn't available in that build; "
              "those were excluded from the ranking above.")


def save_aggregates(all_runs: List[Dict], outdir: str) -> Tuple[str, str]:
    os.makedirs(outdir, exist_ok=True)
    json_path = os.path.join(outdir, "sigmoid_bench_both.json")
    csv_path = os.path.join(outdir, "sigmoid_bench_both.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_runs, f, indent=2)

    cols = ["python_impl", "python_executable", "python_version", "mode",
            "jit_available", "jit_enabled", "jit_requested_env_cpython",
            "jit_requested_env_pypy", "abiflags", "N",
            "overhead_raw_median_s", "exp_raw_median_s", "tanh_raw_median_s",
            "exp_adj_median_s", "tanh_adj_median_s"]
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(",".join(cols) + "\n")
        for run in all_runs:
            jit = run.get("jit", {})
            for row in run["results"]:
                vals = [
                    run.get("python_impl", ""),
                    run["python_executable"],
                    run["python_version"],
                    run.get("mode",""),
                    str(jit.get("available")),
                    str(jit.get("enabled")),
                    str(jit.get("requested_env_cpython")),
                    str(jit.get("requested_env_pypy")),
                    str(jit.get("abiflags", "")),
                    str(row["N"]),
                    f"{row['overhead_raw_median_s']:.9f}",
                    f"{row['exp_raw_median_s']:.9f}",
                    f"{row['tanh_raw_median_s']:.9f}",
                    f"{row['exp_adj_median_s']:.9f}",
                    f"{row['tanh_adj_median_s']:.9f}",
                ]
                f.write(",".join(vals) + "\n")

    return json_path, csv_path


def try_generate_plots(all_runs: List[Dict], outdir: str) -> List[str]:
    paths = []
    try:
        import matplotlib
        matplotlib.use("Agg")  # headless backend
        import matplotlib.pyplot as plt
    except Exception as e:
        print(f"\n[Info] Skipping plots (matplotlib not available): {e}")
        return paths

    os.makedirs(outdir, exist_ok=True)

    # --- Plot 1: lines of ADJUSTED medians vs N for each run & method ---
    fig1 = plt.figure(figsize=(9.5, 5.7))
    ax = plt.gca()
    for run in all_runs:
        label_base = _label_base(run)
        Ns = [r["N"] for r in run["results"]]
        exp_adj = [r["exp_adj_median_s"] for r in run["results"]]
        tanh_adj = [r["tanh_adj_median_s"] for r in run["results"]]
        ax.plot(Ns, exp_adj, marker="o", linestyle="-", label=f"{label_base} (exp)")
        ax.plot(Ns, tanh_adj, marker="s", linestyle="--", label=f"{label_base} (tanh)")
    ax.set_xscale("log")
    ax.set_xlabel("N (number of elements)")
    ax.set_ylabel("Overhead-adjusted median (s)")
    ax.set_title("Sigmoid benchmark (exp vs tanh) across interpreters (JIT modes)")
    ax.grid(True, which="both", linewidth=0.3, alpha=0.5)
    ax.legend(fontsize=8, ncol=2)
    fig1.tight_layout()
    p1 = os.path.join(outdir, "sigmoid_both_lines.png")
    fig1.savefig(p1, dpi=160)
    paths.append(p1)

    # --- Plot 2: bars for the largest N comparing interpreters & methods (ADJUSTED medians) ---
    sizes = sorted({r["N"] for run in all_runs for r in run["results"]})
    largest = sizes[-1]

    labels = []
    values = []
    for run in all_runs:
        row = next(r for r in run["results"] if r["N"] == largest)
        labels.append(f"{_label_base(run)} (exp)");  values.append(row["exp_adj_median_s"])
        labels.append(f"{_label_base(run)} (tanh)"); values.append(row["tanh_adj_median_s"])

    fig2 = plt.figure(figsize=(max(6, 1.6*len(values)), 5.7))
    ax2 = plt.gca()
    ax2.bar(range(len(values)), values)
    ax2.set_xticks(range(len(values)))
    ax2.set_xticklabels(labels, rotation=0, fontsize=8)
    ax2.set_ylabel("Overhead-adjusted median (s)")
    ax2.set_title(f"Largest N = {largest:,} | exp vs tanh per interpreter/mode")
    ax2.grid(True, axis="y", linewidth=0.3, alpha=0.5)
    fig2.tight_layout()
    p2 = os.path.join(outdir, "sigmoid_both_bars.png")
    fig2.savefig(p2, dpi=160)
    paths.append(p2)

    return paths


# ----------------------------------------- CLI -----------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Benchmark sigmoid (exp & tanh) across CPython 3.10/3.14 (JIT off/on) and PyPy (JIT off/on).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python3 sigmoid_bench_both.py
              python3 sigmoid_bench_both.py --pythons python3.10 python3.14 pypy3
              python3 sigmoid_bench_both.py --sizes 10000,100000,1000000 --repeats 7 --warmup 2
        """)
    )
    p.add_argument("--child", action="store_true",
                   help="(internal) run the benchmark in child mode and print JSON")
    p.add_argument("--sizes", type=str, default="10000,100000,1000000",
                   help="Comma-separated sizes, e.g. 10000,100000,1000000")
    p.add_argument("--repeats", type=int, default=5,
                   help="Number of repeats; MEDIAN is reported.")
    p.add_argument("--warmup", type=int, default=1,
                   help="Unmeasured warmup passes per function.")
    p.add_argument("--pythons", nargs="*", default=None,
                   help="Interpreter binaries to compare (e.g. python3.10 python3.14 pypy3)")
    p.add_argument("--outdir", type=str, default=".",
                   help="Directory to write outputs (JSON, CSV, PNG).")
    return p.parse_args()


def coerce_sizes(s: str) -> List[int]:
    out = []
    for tok in s.split(","):
        tok = tok.strip()
        if not tok:
            continue
        # allow 1e6 style
        out.append(int(float(tok)) if "e" in tok.lower() else int(tok.replace("_", "")))
    if not out or not all(n > 0 for n in out):
        raise ValueError("Sizes must be positive")
    return out


# ---------------------- Interpreter launching (parent mode) -----------------------------

def _run_child(exe: str, sizes: List[int], repeats: int, warmup: int,
               jit_mode: str) -> Dict | None:
    """
    Launch a child run under `exe` with JIT mode 'off' or 'on'.
    - CPython: PYTHON_JIT=0/1 (3.14+); harmless on 3.10.
    - PyPy:    PYPY_DISABLE_JIT=1 (off) or unset (on).
    """
    env = os.environ.copy()
    env.pop("PYTHON_JIT", None)
    env.pop("PYPY_DISABLE_JIT", None)

    if jit_mode == "off":
        env["PYTHON_JIT"] = "0"
        env["PYPY_DISABLE_JIT"] = "1"
    elif jit_mode == "on":
        env["PYTHON_JIT"] = "1"  # harmless on PyPy / CPython < 3.14
        # leave PYPY_DISABLE_JIT unset for ON
    else:
        raise ValueError("jit_mode must be 'off' or 'on'")

    cmd = [
        exe, os.path.abspath(__file__),
        "--child",
        "--sizes", ",".join(str(n) for n in sizes),
        "--repeats", str(repeats),
        "--warmup", str(warmup),
    ]

    # ### HERE: we actually invoke the given interpreter as a subprocess
    try:
        cp = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
        return json.loads(cp.stdout)
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {exe} (JIT {jit_mode.upper()}): {e}\nstdout:\n{e.stdout}\nstderr:\n{e.stderr}")
    except json.JSONDecodeError:
        print(f"[FAIL] {exe} (JIT {jit_mode.upper()}): produced non-JSON output:\n{cp.stdout}\n{cp.stderr}")
    return None


def run_parent(pythons: List[str] | None, sizes: List[int], repeats: int, warmup: int, outdir: str) -> None:
    # Auto-detect reasonable defaults if none provided
    if not pythons:
        candidates = ["python3.10", "python3.14", "pypy3"]
        found = [p for p in candidates if shutil.which(p)]
        if sys.executable not in found:
            found.append(sys.executable)
        pythons = found
        print(f"[Info] Auto-selected interpreters: {', '.join(pythons)}")
        if len(pythons) < 2:
            print("[Warn] Fewer than two interpreters found on PATH. "
                  "Pass more explicitly with --pythons for a richer comparison.")

    all_runs: List[Dict] = []
    for exe in pythons:
        print(f"\n[Run] {exe} → JIT OFF …")
        # ### HERE: one call per interpreter with JIT OFF
        off = _run_child(exe, sizes, repeats, warmup, jit_mode="off")
        if off:
            all_runs.append(off)
            print(f"[OK ] {exe} OFF  {off['python_impl']} {off['python_version']}  mode={off['mode']}  "
                  f"JIT avail={off['jit']['available']} enabled={off['jit']['enabled']}")

        print(f"[Run] {exe} → JIT ON  …")
        # ### HERE: one call per interpreter with JIT ON
        on = _run_child(exe, sizes, repeats, warmup, jit_mode="on")
        if on:
            all_runs.append(on)
            print(f"[OK ] {exe} ON   {on['python_impl']} {on['python_version']}  mode={on['mode']}  "
                  f"JIT avail={on['jit']['available']} enabled={on['jit']['enabled']}")

    if not all_runs:
        print("\nNo successful runs; nothing to aggregate.")
        return

    aggregate_and_print(all_runs)

    json_path, csv_path = save_aggregates(all_runs, outdir)
    print(f"\nSaved: {json_path}")
    print(f"Saved: {csv_path}")

    for pth in try_generate_plots(all_runs, outdir):
        print(f"Saved: {pth}")


def main():
    args = parse_args()
    sizes = coerce_sizes(args.sizes)

    if args.child:
        info = run_child_benchmark(sizes=sizes, repeats=args.repeats, warmup=args.warmup)
        # Child prints JSON ONLY:
        print(json.dumps(info))
        return

    run_parent(pythons=args.pythons, sizes=sizes, repeats=args.repeats,
               warmup=args.warmup, outdir=args.outdir)


if __name__ == "__main__":
    main()
