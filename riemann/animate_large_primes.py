#!/usr/bin/env python3
"""Animate actual finite explicit formulas in four large-prime windows.

The upper panel preserves the absolute count error by shifting both
curves by the same exact midpoint. The lower panel removes the center
error only to expose local shape. Its alignment is explicitly labeled.
Every frame is an evaluated zero-pair count; no curves are morphed.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
import numpy as np

from animation_utils import BLUE, INK, MUTED, ORANGE, GRID
from animation_utils import capture, decorate, save_gif, setup_style
from large_scale_formula import compute_window, DEFAULT_COUNTS
from verify_large_prime_windows import verify as verify_data


HERE = Path(__file__).resolve().parent
RADIUS = 200
OFFSETS = np.arange(-RADIUS, RADIUS + 0.25, 0.25)
SLUGS = ("1m", "1b", "1t", "1000t")
TITLES = ("1 million", "1 billion", "1 trillion", "1,000 trillion")


def exact_centered(window: dict, offsets: np.ndarray) -> np.ndarray:
    """Exact local count minus pi(p-) + 1/2, using integer differences."""
    primes = np.asarray(window["prime_offsets_from_focal"], dtype=np.int64)
    before = int(np.count_nonzero(primes < 0))
    return np.searchsorted(primes, offsets, side="right") - before - 0.5


def center_errors(result: dict, window: dict) -> dict[int, float]:
    with localcontext() as context:
        context.prec = 55
        midpoint = Decimal(window["pi_midpoint_exact"])
        return {k: float(Decimal(value) - midpoint)
                for k, value in result["centers_decimal"].items()}


def format_error(value: float, prime: int) -> str:
    # The input zero table does not support sub-prime absolute precision
    # at 10**15. Round that display to a whole prime, with a bound below.
    places = 3 if prime < 10**12 else 1 if prime < 10**15 else 0
    return f"{value:+,.{places}f} primes"


def format_cycle(value: float) -> str:
    if value < 1000:
        return f"{value:,.1f} numbers"
    return f"{value:,.0f} numbers"


def render_window(
    window: dict, result: dict, title: str, slug: str,
    output_dir: Path, lower_limit: float, heights: np.ndarray,
) -> tuple[dict, dict]:
    setup_style()
    prime = window["focal_prime"]
    errors = center_errors(result, window)
    counts = result["counts"]
    local_primes = np.array(window["prime_offsets_from_focal"])
    local_primes = local_primes[np.abs(local_primes) <= RADIUS]
    step_x = np.unique(np.r_[-RADIUS, local_primes, RADIUS])
    step_y = exact_centered(window, step_x)
    raw_max = max(float(np.max(np.abs(step_y))),
                  *(float(np.max(np.abs(errors[k] + result["increments"][k])))
                    for k in counts))
    unit = 10 ** math.floor(math.log10(max(raw_max, 1)))
    upper_limit = max(30, math.ceil(1.2 * raw_max / unit) * unit)

    fig = plt.figure(figsize=(10, 9.4), dpi=100)
    fig.text(0.065, 0.970, f"Zeta zeros near {title}",
             fontsize=22, weight="bold", va="top")
    fig.text(0.065, 0.929,
             f"p = {prime:,}     |     x = p + h,   −200 ≤ h ≤ 200",
             fontsize=12.4, color=MUTED, va="top")
    fig.text(0.065, 0.878, "ZERO PAIRS", fontsize=9.5, color=MUTED)
    count_text = fig.text(0.205, 0.875, "", fontsize=22, color=BLUE, weight="bold")
    fig.text(0.485, 0.878, "ACTUAL ERROR AT p", fontsize=9.5, color=MUTED)
    error_text = fig.text(0.690, 0.875, "", fontsize=19, color=ORANGE, weight="bold")
    fig.text(0.065, 0.846,
             f"Exact reference A = {Decimal(window['pi_midpoint_exact']):,} primes",
             fontsize=10.5, color=MUTED)
    stage_text = fig.text(0.950, 0.846, "", fontsize=10.5, color=MUTED, ha="right")

    fig.text(0.120, 0.795, "Actual reconstruction: both curves subtract the same A",
             fontsize=12.6, weight="bold")
    top = fig.add_axes([0.120, 0.540, 0.830, 0.225])
    bottom = fig.add_axes([0.120, 0.220, 0.830, 0.225])
    fig.text(0.120, 0.479, "Local shape: the reconstruction’s vertical error is removed",
             fontsize=12.6, weight="bold")
    for ax in (top, bottom):
        decorate(ax)
        ax.axhline(0, color="#adb9c7", linewidth=0.8, zorder=1)
        ax.axvline(0, color="#adb9c7", linewidth=0.9, linestyle=(0, (3, 3)), zorder=1)
        ax.step(step_x, step_y, where="post", color=INK, linewidth=1.7, zorder=3)
        ax.set_xlim(-RADIUS, RADIUS)
        ax.set_xticks([-200, -100, 0, 100, 200])
        ax.tick_params(labelsize=10.5)
        ax.scatter([0], [0], s=40, facecolors="white", edgecolors=INK,
                   linewidths=1.7, zorder=6)
    top.set_yscale("symlog", linthresh=20, linscale=1, base=10)
    top.set_ylim(-upper_limit, upper_limit)
    tick_sizes = ([10, 50] if upper_limit < 100 else
                  [10, 100] if upper_limit < 1000 else
                  [100, 1000, 10000, 100000, 1000000])
    tick_sizes = [value for value in tick_sizes if value < upper_limit]
    top.set_yticks([-value for value in reversed(tick_sizes)] + [0] + tick_sizes)
    top.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    top.minorticks_off()
    top.set_ylabel("Prime count − A\n(symmetric log scale)", fontsize=10.5)
    top.tick_params(labelbottom=False)
    bottom.set_ylim(-lower_limit, lower_limit)
    bottom.set_yticks(np.arange(-lower_limit, lower_limit + 0.1, 5))
    bottom.set_ylabel("Count relative to center\n(linear scale)", fontsize=10.5)
    bottom.set_xlabel("Offset h from the chosen prime p", fontsize=11.5, labelpad=10)
    top_curve, = top.plot([], [], color=BLUE, linewidth=2.4, zorder=4)
    shape_curve, = bottom.plot([], [], color=BLUE, linewidth=2.4, zorder=4)
    handles = [Line2D([0], [0], color=INK, linewidth=1.8, label="Exact prime staircase"),
               Line2D([0], [0], color=BLUE, linewidth=2.4, label="Reconstruction from zeros")]
    top.legend(handles=handles, loc="upper right", fontsize=9.5,
               frameon=True, framealpha=0.96, edgecolor="white", ncol=2,
               columnspacing=1.3, handlelength=2.0)

    fig.text(0.065, 0.125,
             "The circle at h = 0 marks the exact midpoint of the prime’s jump.",
             fontsize=10.3, color=MUTED)
    cycle_text = fig.text(0.065, 0.095, "", fontsize=10.3, color=MUTED)
    uncertainty_text = fig.text(0.065, 0.065, "", fontsize=9.8, color=MUTED)
    fig.text(0.065, 0.035,
             "Each stage is a computed finite sum. More zeros need not reduce the error at this location.",
             fontsize=10, color=MUTED)

    frames = []
    per_stage = []
    for index, count in enumerate(counts):
        increment = result["increments"][count]
        top_curve.set_data(OFFSETS, errors[count] + increment)
        shape_curve.set_data(OFFSETS, increment)
        count_text.set_text(f"{count:,}")
        error_text.set_text(format_error(errors[count], prime))
        stage_text.set_text(f"Stage {index + 1} / {len(counts)}")
        cycle = float(2 * np.pi * prime / heights[count - 1]) if count else None
        cycle_text.set_text("Shortest retained local cycle: " + (
            format_cycle(cycle) if cycle is not None else "no zero oscillations yet"))
        source_bound = result["metadata"]["zero_table_center_error_bounds"][count]
        if count:
            uncertainty_text.set_text(
                f"Zero-table precision alone permits up to ±{source_bound:.3g} primes of center error; "
                "finite-sum error is separate.")
        else:
            uncertainty_text.set_text("K = 0 retains the smooth terms and prime-power corrections.")
        frames.append(capture(fig))
        per_stage.append({
            "zero_pairs": count,
            "reconstruction_at_prime_decimal": result["centers_decimal"][count],
            "error_at_midpoint": errors[count],
            "local_cycle_scale": cycle,
            "zero_table_center_error_bound": source_bound,
            "zero_table_increment_error_bound": result["metadata"]["zero_table_increment_error_bounds"][count],
            "increment_min": float(increment.min()),
            "increment_max": float(increment.max()),
        })
    path = output_dir / f"large_prime_{slug}.gif"
    durations = [1400] + [1100] * (len(frames) - 2) + [4200]
    gif_metadata = save_gif(frames, path, durations)
    frames[-1].save(path.with_suffix(".png"))
    plt.close(fig)
    report = {
        "scale": title, "prime": prime, "anchor_count": window["pi_anchor"],
        "exact_midpoint": window["pi_midpoint_exact"],
        "window_radius": RADIUS, "offset_step": 0.25,
        "primes_in_plot": len(local_primes), "mobius_cutoff": result["mobius_cutoff"],
        "upper_symmetric_log_limits": [-upper_limit, upper_limit],
        "upper_linear_threshold": 20,
        "lower_linear_limits": [-lower_limit, lower_limit],
        "stages": per_stage, "numerical_validation": result["metadata"],
    }
    return gif_metadata, report


def generate_all(output_dir: Path) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    references = json.loads((HERE / "data" / "large_prime_windows.json").read_text())
    verify_data(references)
    windows = references["windows"]
    heights = np.loadtxt(HERE / "data" / "odlyzko_zeros_10000.txt")
    results = []
    for window in windows:
        print(f"Evaluating zero sums near {window['focal_prime']:,}...", flush=True)
        # The reconstruction receives only the center, offsets, and zero
        # counts. Its evaluator reads zero heights, never prime lists.
        results.append(compute_window(window["focal_prime"], OFFSETS, DEFAULT_COUNTS))
    shape_max = max(
        *(float(np.max(np.abs(exact_centered(w, OFFSETS)))) for w in windows),
        *(float(np.max(np.abs(r["increments"][k]))) for r in results for k in r["counts"]),
    )
    lower_limit = 5 * math.ceil(shape_max * 1.15 / 5)
    manifest, reports = [], []
    for window, result, title, slug in zip(windows, results, TITLES, SLUGS):
        metadata, report = render_window(window, result, title, slug,
                                         output_dir, lower_limit, heights)
        manifest.append(metadata)
        reports.append(report)
        print(f"Saved {metadata['file']} ({metadata['size_bytes']:,} bytes)", flush=True)
    report_path = (HERE if output_dir.resolve() == (HERE / "assets").resolve()
                   else output_dir) / "large_prime_validation.json"
    report_path.write_text(json.dumps({
        "schema_version": 1,
        "formula": "Finite paired explicit formula with complete fixed Mobius sum in each window",
        "upper_panel": "F_K(p+h)-A and pi(p+h)-A, A=pi(p-)+1/2",
        "lower_panel": "F_K(p+h)-F_K(p) and pi(p+h)-A; the reconstruction center error is removed",
        "prime_reference": "data/large_prime_windows.json",
        "zero_data": "data/odlyzko_zeros_10000.txt",
        "caveat": "Numerical cross-checks are empirical, source bounds assume the published table precision, and neither controls finite-zero truncation error.",
        "windows": reports,
    }, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE / "assets")
    args = parser.parse_args()
    print(json.dumps(generate_all(args.output_dir), indent=2))
