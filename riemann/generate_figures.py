#!/usr/bin/env python3
"""Rebuild all Riemann article figures and their numerical validation.

From the repository root:
    python -m pip install -r riemann/requirements.txt
    python riemann/generate_figures.py

The bundled zero table makes this command independent of network access.
No precomputed curve cache is required or written. Typical runtime is
under two minutes on a modern laptop; it depends on numerical libraries.
"""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FormatStrFormatter, MultipleLocator
import numpy as np
from scipy.special import expi

from explicit_formula import (
    DOMAIN, MOBIUS_WEIGHTS, load_zero_heights, reconstruct_direct,
    reconstruct_fast, sieve_primes,
)


HERE = Path(__file__).resolve().parent
COUNTS = (0, 10, 50, 200, 1000, 10000)
INK, BLUE, ORANGE, MUTED = "#17283d", "#2166d6", "#d77924", "#526174"
SOURCE_URL = "https://www-users.cse.umn.edu/~odlyzko/zeta_tables/zeros1"
TABLE_ERROR_BOUND = 3e-9


def configure_style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 11,
        "axes.labelsize": 12, "axes.titlesize": 13,
        "axes.titleweight": "bold", "text.color": INK,
        "axes.labelcolor": INK, "savefig.facecolor": "white",
        "path.simplify": False,
    })


def decorate(ax: plt.Axes) -> None:
    ax.grid(axis="y", color="#e4e9f0", lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0, pad=7, colors=MUTED)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#cad4df")


def prime_staircase(ax: plt.Axes, primes: np.ndarray, linewidth: float = 2.0) -> None:
    sx = np.r_[2.0, primes[primes > 2], 100.0]
    sy = np.searchsorted(primes, sx, side="right")
    ax.step(sx, sy, where="post", color=INK, lw=linewidth, zorder=3)


def draw_prime_count(primes: np.ndarray, output: Path) -> None:
    """Show the introductory exact count, including 0 and 1."""
    x = np.arange(101)
    counts = np.searchsorted(primes, x, side="right")
    fig, ax = plt.subplots(figsize=(11.4, 6.5), dpi=190)
    fig.subplots_adjust(left=0.10, right=0.96, bottom=0.20, top=0.79)
    fig.text(0.10, 0.94, "Counting primes from 0 to 100",
             fontsize=23, weight="bold")
    fig.text(0.10, 0.885, "Each prime increases the running total by one",
             fontsize=13, color=MUTED)
    ax.step(x, counts, where="post", color=INK, lw=2.2, zorder=3)
    ax.set(xlim=(0, 100), ylim=(0, 27))
    ax.set_xlabel(r"Number $x$", labelpad=10)
    ax.set_ylabel(r"Primes so far, $\pi(x)$", labelpad=10)
    ax.set_xticks(np.arange(0, 101, 10))
    ax.set_yticks(np.arange(0, 26, 5))
    decorate(ax)
    ax.scatter([10, 100], [4, 25], color=INK, s=30, zorder=4, clip_on=False)
    ax.annotate(r"$\pi(10)=4$", (10, 4), xytext=(8, -24),
                textcoords="offset points", fontsize=11, color=MUTED)
    ax.annotate(r"$\pi(100)=25$", (100, 25), xytext=(-10, 12),
                textcoords="offset points", ha="right", fontsize=11, color=INK)
    fig.text(0.10, 0.09,
             "The count is zero before 2. Each step marks a prime; by 100, there are 25 primes.",
             fontsize=10.8, color=MUTED)
    fig.savefig(output, dpi=190)
    plt.close(fig)


def draw_baseline(primes: np.ndarray, output: Path) -> None:
    x = np.linspace(*DOMAIN, 4000)
    fig, ax = plt.subplots(figsize=(11.4, 6.5), dpi=190)
    fig.subplots_adjust(left=0.09, right=0.965, bottom=0.20, top=0.78)
    fig.text(0.09, 0.94, "Counting primes: steps and a smooth estimate",
             fontsize=22, weight="bold")
    fig.text(0.09, 0.885, r"The exact count $\pi(x)$ and the logarithmic integral $\mathrm{li}(x)$",
             fontsize=13, color=MUTED)
    prime_staircase(ax, primes)
    ax.plot(x, expi(np.log(x)), color=ORANGE, lw=2.0, zorder=4)
    ax.set(xlim=DOMAIN, ylim=(0, 32))
    ax.set_xlabel(r"Cutoff $x$", labelpad=10)
    ax.set_ylabel("Number of primes", labelpad=10)
    ax.xaxis.set_major_locator(MultipleLocator(10))
    ax.yaxis.set_major_locator(MultipleLocator(5))
    decorate(ax)
    handles = [Line2D([0], [0], color=INK, lw=2, label=r"Exact count $\pi(x)$"),
               Line2D([0], [0], color=ORANGE, lw=2, label=r"Smooth estimate $\mathrm{li}(x)$")]
    ax.legend(handles=handles, frameon=False, loc="upper left", fontsize=11.5)
    ax.annotate("25 primes", (100, 25), xytext=(-7, -19), textcoords="offset points",
                ha="right", color=INK, fontsize=11)
    fig.text(0.09, 0.09, r"Each prime adds one step. Here $\mathrm{li}(x)=\mathrm{Ei}(\log x)$, with the principal-value convention.",
             fontsize=10.8, color=MUTED)
    fig.savefig(output, dpi=190)
    plt.close(fig)


def draw_progression(
    x: np.ndarray, curves: dict[int, np.ndarray], primes: np.ndarray, output: Path,
) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(14.2, 9.0), dpi=190, sharex=True, sharey=True)
    fig.subplots_adjust(left=0.065, right=0.975, bottom=0.17, top=0.78,
                        hspace=0.42, wspace=0.19)
    fig.text(0.065, 0.945, "More zero pairs reveal the prime staircase",
             fontsize=24, weight="bold")
    fig.text(0.065, 0.897, "The same interval and scale in every panel: 20 to 40",
             fontsize=13, color=MUTED)
    handles = [Line2D([0], [0], color=INK, lw=2.1, label=r"Exact count $\pi(x)$"),
               Line2D([0], [0], color=BLUE, lw=1.55, label="Explicit-formula reconstruction")]
    fig.legend(handles=handles, frameon=False, loc="upper left",
               bbox_to_anchor=(0.06, 0.867), ncol=2, fontsize=11.5,
               handlelength=2.8, columnspacing=2.5)

    for ax, count in zip(axes.flat, COUNTS):
        prime_staircase(ax, primes, linewidth=2.0)
        ax.plot(x, curves[count], color=BLUE, lw=1.3, zorder=4)
        ax.set(xlim=(20, 40), ylim=(7.5, 12.7))
        ax.set_title(f"{count:,} zero pairs" if count else "0 pairs: smooth terms only",
                     loc="left", fontsize=12.5, pad=10)
        ax.xaxis.set_major_locator(MultipleLocator(5))
        ax.yaxis.set_major_locator(MultipleLocator(1))
        decorate(ax)
        for p in (23, 29, 31, 37):
            ax.axvline(p, color=INK, alpha=0.08, lw=0.7, zorder=1)
    for ax in axes[-1]:
        ax.set_xlabel(r"Cutoff $x$", labelpad=9)
    for ax in axes[:, 0]:
        ax.set_ylabel("Prime count", labelpad=9)
    fig.text(0.065, 0.095,
             "One pair is the zero at +t and its conjugate at -t. The sieve is used only for the dark comparison curve.",
             fontsize=10.7, color=MUTED)
    fig.text(0.065, 0.06,
             "Finite sums ripple near jumps. Greater resolution does not mean smaller error at every individual point.",
             fontsize=10.7, color=MUTED)
    fig.savefig(output, dpi=190)
    plt.close(fig)


def draw_reconstruction(x: np.ndarray, y: np.ndarray, primes: np.ndarray, output: Path) -> None:
    """Preserve the overview, close-up and prime-29 detail of the original plot."""
    fig = plt.figure(figsize=(12.2, 9.3), dpi=200, facecolor="white")
    gs = fig.add_gridspec(2, 3, left=0.085, right=0.97, top=0.81, bottom=0.17,
                          hspace=0.54, wspace=0.43, height_ratios=[1, 1.06])
    overview = fig.add_subplot(gs[0, :])
    zoom = fig.add_subplot(gs[1, :2])
    detail = fig.add_subplot(gs[1, 2])
    fig.text(0.085, 0.955, "Exact primes vs. 10,000 zero pairs", fontsize=23, weight="bold")
    fig.text(0.085, 0.914, "Riemann's explicit formula reconstructs the prime-counting staircase",
             fontsize=12.5, color=MUTED)
    handles = [Line2D([0], [0], color=INK, lw=2.6, label=r"Exact prime count $\pi(x)$"),
               Line2D([0], [0], color=BLUE, lw=1.5, label="Reconstruction: 10,000 zero pairs")]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.079, 0.883),
               frameon=False, ncol=2, handlelength=2.8, columnspacing=2.5, fontsize=11)
    for ax in (overview, zoom, detail):
        prime_staircase(ax, primes, linewidth=2.5)
        ax.plot(x, y, color=BLUE, lw=1.2, zorder=4)
        ax.set_xlabel(r"Cutoff $x$", labelpad=9)
        decorate(ax)
    overview.set(xlim=(2, 100), ylim=(0, 27))
    overview.set_title("Overview: all 25 primes up to 100", loc="left", pad=12)
    overview.set_ylabel(r"Number of primes, $\pi(x)$", labelpad=10)
    overview.xaxis.set_major_locator(MultipleLocator(10))
    overview.yaxis.set_major_locator(MultipleLocator(5))
    overview.axvspan(20, 40, color=BLUE, alpha=0.04, zorder=0)

    zoom.set(xlim=(20, 40), ylim=(7.6, 12.5))
    zoom.set_title("Close-up: the two curves almost overlap", loc="left", pad=12)
    zoom.set_ylabel(r"Number of primes, $\pi(x)$", labelpad=10)
    zoom.xaxis.set_major_locator(MultipleLocator(4))
    zoom.yaxis.set_major_locator(MultipleLocator(1))
    for p in (23, 29, 31, 37):
        zoom.axvline(p, color=INK, alpha=0.09, lw=0.7, zorder=1)
        zoom.text(p, 7.67, str(p), ha="center", va="bottom", color="#6a7889", fontsize=9,
                  bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})

    detail.set(xlim=(28.97, 29.03), ylim=(8.8, 10.2))
    detail.set_title("Detail at prime 29", loc="left", pad=12)
    detail.set_xticks([28.98, 29.0, 29.02])
    detail.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    detail.set_yticks([9.0, 9.5, 10.0])
    detail.tick_params(labelsize=10)
    detail.axvline(29, color=INK, alpha=0.12, lw=0.8, zorder=0)
    detail.text(0.045, 0.94, "Remaining\nripples", va="top",
                transform=detail.transAxes, color=MUTED, fontsize=9.4)
    fig.text(0.085, 0.096,
             "10,000 positive-height zeros plus their conjugates = 20,000 nontrivial zeros in the sum.",
             fontsize=10.6, color=MUTED)
    fig.text(0.085, 0.063,
             "Zero heights: Andrew Odlyzko. At a prime, the infinite formula returns the midpoint of the jump.",
             fontsize=10.2, color=MUTED)
    fig.savefig(output, dpi=200, facecolor="white")
    plt.close(fig)


def draw_zeros(heights: np.ndarray, output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 6.4), dpi=190,
                             gridspec_kw={"width_ratios": [0.9, 1.15]})
    fig.subplots_adjust(left=0.075, right=0.96, bottom=0.20, top=0.78, wspace=0.34)
    fig.text(0.075, 0.94, "Where the zeta zeros live", fontsize=23, weight="bold")
    fig.text(0.075, 0.885, r"A complex input $s=\sigma+it$ has a horizontal real part and a vertical imaginary part",
             fontsize=12.1, color=MUTED)
    ax = axes[0]
    ax.axhline(0, color="#aebac8", lw=1)
    ax.scatter([-2, -4, -6, -8], [0, 0, 0, 0], color=ORANGE, s=44, zorder=4)
    ax.set(xlim=(-8.8, 1.2), ylim=(-1.6, 1.6))
    ax.set_xticks([-8, -6, -4, -2, 0, 1])
    ax.set_yticks([-1, 0, 1])
    ax.set_title("Trivial zeros", loc="left", pad=12)
    ax.set_xlabel(r"Real part $\sigma$", labelpad=9)
    ax.set_ylabel(r"Imaginary part $t$", labelpad=9)
    decorate(ax)
    ax.text(-5.0, 0.45, r"$-2,-4,-6,-8,\ldots$", color=ORANGE, ha="center", fontsize=13)
    ax = axes[1]
    shown = heights[heights < 50]
    both = np.r_[-shown[::-1], shown]
    ax.axvspan(0, 1, color=BLUE, alpha=0.035)
    ax.axvline(0.5, color=BLUE, lw=1.3, alpha=0.75)
    ax.axhline(0, color="#d8e0e9", lw=0.7)
    ax.scatter(np.full_like(both, 0.5), both, color=BLUE, s=24, zorder=4)
    ax.set(xlim=(-0.08, 1.08), ylim=(-54, 54))
    ax.set_xticks([0, 0.5, 1])
    ax.set_title("First 10 conjugate pairs", loc="left", pad=12)
    ax.set_xlabel(r"Real part $\sigma$", labelpad=9)
    ax.set_ylabel(r"Imaginary part $t$", labelpad=9)
    decorate(ax)
    for gamma, label in [(shown[0], "14.1347"), (shown[1], "21.0220")]:
        ax.annotate(label, (0.5, gamma), xytext=(9, -3), textcoords="offset points",
                    fontsize=9.5, color=MUTED)
    fig.text(0.075, 0.09,
             "These are locations where the analytically continued zeta function is zero. The panels use different scales.",
             fontsize=10.6, color=MUTED)
    fig.savefig(output, dpi=190)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, default=HERE / "assets")
    parser.add_argument("--validation-file", type=Path, default=HERE / "validation.json")
    parser.add_argument("--threads", type=int, default=2, help="FINUFFT worker threads (default: 2)")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    configure_style()
    started = time.perf_counter()
    data_path = HERE / "data" / "odlyzko_zeros_10000.txt"
    heights = load_zero_heights(data_path)
    primes = sieve_primes(100)

    half_integers = np.arange(2.5, 100, 1.0)
    rng = np.random.default_rng(42)
    checks = np.unique(np.r_[half_integers,
                            np.exp(rng.uniform(np.log(2), np.log(100), 48)),
                            (np.array([23, 29, 31, 37])[:, None]
                             + np.array([-0.001, 0.0, 0.001])).ravel(),
                            DOMAIN])
    zoom_grid = np.linspace(20.0, 40.0, 20001)
    x_small = np.unique(np.r_[zoom_grid, checks])
    # Log spacing resolves the fastest waves in gamma*log(x). Extra
    # linear grids preserve the overview's two magnified windows.
    x_large = np.unique(np.r_[np.geomspace(2.0, 100.0, 100001), zoom_grid,
                             np.linspace(28.97, 29.03, 1201), checks])
    curves: dict[int, np.ndarray] = {}
    check_curves: dict[int, np.ndarray] = {}
    tails: dict[str, dict[str, float]] = {}
    y_large: np.ndarray | None = None
    for count in COUNTS:
        grid = x_large if count == 10000 else x_small
        print(f"Reconstructing with {count:,} zero pairs...", flush=True)
        values, tail = reconstruct_fast(grid, heights[:count], threads=args.threads)
        curves[count] = values[np.searchsorted(grid, zoom_grid)]
        check_curves[count] = values[np.searchsorted(grid, checks)]
        tails[str(count)] = tail
        if count == 10000:
            y_large = values

    print("Checking the accelerated curves against direct complex Ei evaluation...", flush=True)
    direct = reconstruct_direct(checks, heights, COUNTS)
    discrepancies = {str(k): float(np.max(np.abs(check_curves[k] - direct[k]))) for k in COUNTS}
    max_discrepancy = max(discrepancies.values())
    if max_discrepancy > 1e-8:
        raise RuntimeError(f"Accelerated evaluation failed the 1e-8 check: {max_discrepancy:g}")
    half_idx = np.searchsorted(checks, half_integers)
    exact = np.searchsorted(primes, half_integers, side="right")
    errors = {}
    for count in COUNTS:
        absolute = np.abs(check_curves[count][half_idx] - exact)
        errors[str(count)] = {
            "mean_absolute_error": float(np.mean(absolute)),
            "maximum_absolute_error": float(np.max(absolute)),
        }
    # A conservative propagation bound for input rounding, conditional on
    # the source's stated per-height error. d Ei(rho*u)/d gamma = i exp(rho*u)/rho.
    # Use x=100 and gamma-epsilon to bound every x in this fixed domain.
    height_rounding_bound = float(
        2 * TABLE_ERROR_BOUND
        * sum(abs(w) * 100 ** (1 / (2 * m)) for m, w in MOBIUS_WEIGHTS)
        * np.sum(1 / np.sqrt(0.25 + (heights - TABLE_ERROR_BOUND) ** 2))
    )
    assert y_large is not None
    draw_prime_count(primes, args.output_dir / "prime_count_0_to_100.png")
    draw_baseline(primes, args.output_dir / "prime_count_and_logarithmic_integral.png")
    draw_progression(zoom_grid, curves, primes, args.output_dir / "zero_pair_progression.png")
    draw_reconstruction(x_large, y_large, primes,
                        args.output_dir / "primes_exact_vs_10000_zero_pairs.png")
    draw_zeros(heights, args.output_dir / "zeta_zeros.png")
    report = {
        "domain": list(DOMAIN),
        "zero_pair_counts": list(COUNTS),
        "zero_table": {
            "file": "data/odlyzko_zeros_10000.txt",
            "sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
            "source": SOURCE_URL,
            "source_stated_absolute_height_error": TABLE_ERROR_BOUND,
            "count": len(heights),
            "first_height": float(heights[0]),
            "last_height": float(heights[-1]),
            "conservative_height_error_propagation_bound_on_domain": height_rounding_bound,
        },
        "fixed_mobius_cutoff": 6,
        "overview_plot_points": len(x_large),
        "progression_plot_points_per_panel": len(zoom_grid),
        "direct_ei_check": {
            "sample_points": len(checks),
            "sample_description": "98 half-integers, 48 seeded log-uniform points, 12 at/near four primes, and two endpoints",
            "acceptance_tolerance": 1e-8,
            "max_absolute_discrepancy_by_zero_pairs": discrepancies,
            "max_absolute_discrepancy": max_discrepancy,
        },
        "errors_against_exact_prime_count": {
            "sample_points": len(half_integers),
            "sample_description": "x=2.5, 3.5, ..., 99.5; these avoid the jumps",
            "by_zero_pairs": errors,
        },
        "chebyshev_final_128_coefficient_maxima": tails,
        "software": {"python": platform.python_version(),
                     **{name: version(name) for name in ("numpy", "scipy", "matplotlib", "finufft")}},
        "validation_scope": (
            "Numerical checks compare the accelerated evaluator with the same finite formula evaluated directly. "
            "They do not certify a uniform truncation bound, prove the completeness of the zero table, or prove RH. "
            "Prime-count errors are sampled away from jumps; finite sums retain ringing near primes."
        ),
    }
    args.validation_file.parent.mkdir(parents=True, exist_ok=True)
    args.validation_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"half_integer_errors": errors,
                      "max_fast_vs_direct_discrepancy": max_discrepancy,
                      "elapsed_seconds": round(time.perf_counter() - started, 2)}, indent=2))
    print(f"Figures: {args.output_dir}", flush=True)
    print(f"Validation: {args.validation_file}", flush=True)


if __name__ == "__main__":
    main()
