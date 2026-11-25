#!/usr/bin/env python3
"""Animate exact prime-count discrepancies and the classical RH envelope.

This is a finite numerical illustration of the bound already discussed in
the article, |pi(x) - li(x)| < sqrt(x) log(x)/(8 pi), for x >= 2657 under RH.
The sieve supplies exact counts at the plotted integer cutoffs. The
animation is not a proof of a statement about all real x.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.special import expi

from animation_utils import (
    BLUE, INK, MUTED, ORANGE, capture, decorate, new_figure, save_gif,
)
from explicit_formula import sieve_primes


HERE = Path(__file__).resolve().parent


def generate_all(output_dir: Path) -> list[dict[str, object]]:
    primes = sieve_primes(1_000_000)
    assert len(primes) == 78_498
    x = np.unique(np.rint(np.geomspace(2657, 1_000_000, 6000)).astype(int))
    counts = np.searchsorted(primes, x, side="right")
    smooth = expi(np.log(x))
    error = counts - smooth
    bound = np.sqrt(x) * np.log(x) / (8 * np.pi)
    assert np.all(np.abs(error) < bound)
    cutoffs = np.unique(np.rint(np.geomspace(2657, 1_000_000, 90)).astype(int))

    fig = new_figure(
        "A bound on the prime-count error",
        "Exact counts and the classical RH bound, from 2,657 to 1,000,000",
        "The envelope applies for x ≥ 2657 under RH. The blue curve is computed with a sieve.\n"
        "This animation illustrates a finite range; the theorem supplies the general guarantee.",
    )
    ax = fig.add_axes((0.09, 0.25, 0.855, 0.40))
    ax.set_xscale("log")
    ax.set(xlim=(2657, 1_000_000), ylim=(-600, 600),
           xlabel="Cutoff x (logarithmic scale)", ylabel="Prime-count error")
    ax.set_xticks([3000, 10_000, 100_000, 1_000_000],
                  ["3,000", "10,000", "100,000", "1,000,000"])
    ax.minorticks_off()
    decorate(ax)
    ax.fill_between(x, -bound, bound, color=ORANGE, alpha=0.08)
    ax.plot(x, bound, color=ORANGE, linewidth=1.7,
            label=r"Bound: $\pm\sqrt{x}\log(x)/(8\pi)$")
    ax.plot(x, -bound, color=ORANGE, linewidth=1.7)
    ax.axhline(0, color=MUTED, linewidth=0.7, alpha=0.45)
    trace, = ax.plot([], [], color=BLUE, linewidth=1.6,
                     label=r"Error: $\pi(x)-\mathrm{li}(x)$")
    point, = ax.plot([], [], "o", color=BLUE, markersize=6)
    cursor = ax.axvline(cutoffs[0], color=BLUE, linestyle="--", linewidth=0.9, alpha=0.35)
    ax.legend(loc="upper left", frameon=False, fontsize=10.6)
    cutoff_text = fig.text(0.09, 0.78, "", fontsize=17, weight="bold")
    exact_text = fig.text(0.40, 0.78, "", fontsize=14, color=INK)
    smooth_text = fig.text(0.70, 0.78, "", fontsize=14, color=ORANGE)
    error_text = fig.text(0.09, 0.71, "", fontsize=12, color=BLUE)
    relative_text = fig.text(0.53, 0.71, "", fontsize=12, color=MUTED)

    frames = []
    for cutoff in cutoffs:
        exact = int(np.searchsorted(primes, cutoff, side="right"))
        estimate = float(expi(np.log(cutoff)))
        discrepancy = exact - estimate
        stop = int(np.searchsorted(x, cutoff, side="right"))
        trace.set_data(np.r_[x[:stop], cutoff], np.r_[error[:stop], discrepancy])
        point.set_data([cutoff], [discrepancy])
        cursor.set_xdata([cutoff, cutoff])
        cutoff_text.set_text(f"x = {cutoff:,}")
        exact_text.set_text(f"Exact count: {exact:,}")
        smooth_text.set_text(f"li(x): {estimate:,.1f}")
        error_text.set_text(f"Error = {discrepancy:+.2f} primes")
        relative_text.set_text(f"Error magnitude / li(x) = {abs(discrepancy)/estimate:.3%}")
        frames.append(capture(fig))
    plt.close(fig)
    durations = [140] * len(frames)
    durations[0], durations[-1] = 1200, 3200
    result = save_gif(frames, output_dir / "prime_count_error_bound.gif", durations)
    result["validation"] = {
        "integer_cutoffs_checked": int(len(x)),
        "domain": [2657, 1_000_000],
        "pi_1000000": int(len(primes)),
        "li_1000000": float(smooth[-1]),
        "error_1000000": float(error[-1]),
        "bound_1000000": float(bound[-1]),
        "all_sampled_errors_inside_envelope": True,
    }
    return [result]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE / "assets")
    args = parser.parse_args()
    print(json.dumps(generate_all(args.output_dir), indent=2))


if __name__ == "__main__":
    main()
