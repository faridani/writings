#!/usr/bin/env python3
"""Animate prime powers, Mobius inversion, zero sums, and magnification.

All curves are computed from exact finite counts or the same explicit-formula
implementation as the static figures. Zero-count stages are actual finite
sums: no interpolated curve is labeled as a new number of zeros.

From the repository root:
    python riemann/animate_reconstruction.py
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, MaxNLocator
import numpy as np

from animation_utils import (
    BLUE, GREEN, INK, MUTED, ORANGE, capture, decorate, new_figure, save_gif,
)
from explicit_formula import (
    MOBIUS_WEIGHTS, load_zero_heights, reconstruct_direct, reconstruct_fast,
    sieve_primes,
)

HERE = Path(__file__).resolve().parent
COUNTS = (0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000)
NAMES = ("prime_powers", "mobius_correction", "zero_reconstruction", "gibbs_zoom")


def weighted_count(x: np.ndarray, m: int = 1) -> np.ndarray:
    """Exact jumps for J(x**(1/m)), tested via integer powers, not float roots."""
    x = np.asarray(x, dtype=float)
    out = np.zeros_like(x)
    limit = float(x.max())
    for p in sieve_primes(int(limit)):
        base = int(p) ** m
        power, k = base, 1
        while power <= limit:
            out += (x >= power) / k
            power *= base
            k += 1
    return out


def prime_power_events(limit: int) -> dict[int, tuple[int, int]]:
    events = {}
    for p in sieve_primes(limit):
        power, k = int(p), 1
        while power <= limit:
            events[power] = (int(p), k)
            power *= int(p)
            k += 1
    return events


def draw_exact(ax: plt.Axes, xmin: float, xmax: float) -> None:
    primes = sieve_primes(int(np.ceil(xmax)))
    sx = np.r_[xmin, primes[(primes > xmin) & (primes <= xmax)], xmax]
    ax.step(sx, np.searchsorted(primes, sx, side="right"), where="post",
            color=INK, lw=2.4, label=r"Exact $\pi(x)$", zorder=3)


def animate_prime_powers(output_dir: Path) -> dict:
    events = prime_power_events(30)
    x = np.arange(0, 30.5, 0.5)
    j = weighted_count(x)
    pi = np.searchsorted(sieve_primes(30), x, side="right")
    assert abs(weighted_count(np.array([10.0]))[0] - 16 / 3) < 1e-12
    frames, durations = [], []
    for i, cutoff in enumerate(x):
        n = int(cutoff)
        event = events.get(n) if cutoff == n else None
        if event:
            p, k = event
            if k == 1:
                description = f"{n} is prime: both counts increase by 1"
                color = GREEN
            else:
                description = f"{n} = {p}^{k}: J increases by 1/{k}; the prime count stays flat"
                color = ORANGE
        elif cutoff != n:
            description, color = "Between jumps, both counts stay flat", MUTED
        else:
            description, color = f"x = {n}: no new prime or prime power", MUTED
        fig = new_figure(
            "Prime powers add fractional steps",
            "A prime adds 1; its square adds 1/2, its cube adds 1/3, and so on.",
            "These are right-continuous counts: a prime power at the cutoff is included.",
        )
        fig.text(0.10, 0.79, description, fontsize=12.5, color=color)
        ax = fig.add_axes((0.10, 0.24, 0.85, 0.48))
        ax.step(x[:i+1], pi[:i+1], where="post", color=INK, lw=2.6,
                label=r"Primes: $\pi(x)$")
        ax.step(x[:i+1], j[:i+1], where="post", color=BLUE, lw=2.1,
                label=r"Weighted prime powers: $J(x)$")
        ax.axvline(cutoff, color=color, lw=1, alpha=0.4)
        ax.scatter([cutoff, cutoff], [pi[i], j[i]], color=[INK, BLUE], s=34, zorder=5)
        ax.set(xlim=(0, 30), ylim=(0, 14), xlabel="Cutoff x", ylabel="Accumulated count")
        ax.set_xticks(np.arange(0, 31, 5))
        ax.set_yticks(np.arange(0, 15, 2))
        decorate(ax)
        ax.legend(loc="upper left", frameon=False, fontsize=11.5)
        exact_j = sum((Fraction(1, k) for power, (_, k) in events.items()
                       if power <= cutoff), Fraction())
        assert abs(float(exact_j) - j[i]) < 1e-12
        fig.text(0.10, 0.14, f"x = {cutoff:g}", fontsize=16, weight="bold")
        fig.text(0.35, 0.14, f"Prime count = {pi[i]}", fontsize=16, color=INK)
        fig.text(0.66, 0.14, f"J(x) = {float(exact_j):.3f}", fontsize=16, color=BLUE)
        frames.append(capture(fig))
        plt.close(fig)
        durations.append(800 if event else 150)
    durations[0], durations[-1] = 700, 2200
    return save_gif(frames, output_dir / "prime_powers.gif", durations)


def animate_mobius_correction(output_dir: Path) -> dict:
    x = np.arange(0.0, 101.0)
    exact = np.searchsorted(sieve_primes(100), x, side="right")
    stages, current = [], np.zeros_like(x)
    for m, weight in MOBIUS_WEIGHTS:
        current = current + weight * weighted_count(x, m)
        stages.append(current.copy())
    assert np.max(np.abs(stages[-1] - exact)) < 1e-12
    titles = (
        r"Begin with $J(x)$: primes and their higher powers",
        r"Subtract $\frac{1}{2}J(\sqrt{x})$",
        r"Subtract $\frac{1}{3}J(x^{1/3})$",
        r"Subtract $\frac{1}{5}J(x^{1/5})$",
        r"Add back $\frac{1}{6}J(x^{1/6})$: only the prime count remains",
    )
    formulas = (
        r"$J(x)$",
        r"$J(x)-\frac{1}{2}J(\sqrt{x})$",
        r"$J(x)-\frac{1}{2}J(\sqrt{x})-\frac{1}{3}J(x^{1/3})$",
        r"$J(x)-\frac{1}{2}J(\sqrt{x})-\frac{1}{3}J(x^{1/3})-\frac{1}{5}J(x^{1/5})$",
        r"$J(x)-\frac{1}{2}J(\sqrt{x})-\frac{1}{3}J(x^{1/3})-\frac{1}{5}J(x^{1/5})+\frac{1}{6}J(x^{1/6})$",
    )
    frames = []
    for i, y in enumerate(stages):
        fig = new_figure(
            "Removing the extra prime-power counts",
            "Mobius inversion subtracts repeated counts and restores over-subtracted terms.",
            "Exact counting identity on 2 to 100. Terms with m >= 7 vanish because 100 < 2^7.",
        )
        fig.text(0.10, 0.79, f"{i+1}/5   " + titles[i], fontsize=12.5,
                 color=GREEN if i == 4 else BLUE)
        upper = fig.add_axes((0.10, 0.48, 0.85, 0.25))
        upper.step(x, exact, where="post", color=INK, lw=2.8, label=r"Exact $\pi(x)$")
        upper.step(x, y, where="post", color=BLUE, lw=1.7, label="Current weighted total")
        upper.set(xlim=(2, 100), ylim=(0, 31), ylabel="Running total")
        upper.tick_params(labelbottom=False)
        upper.legend(loc="upper left", frameon=False, fontsize=10.5)
        decorate(upper)
        lower = fig.add_axes((0.10, 0.22, 0.85, 0.17))
        lower.axhline(0, color=INK, lw=1)
        lower.step(x, y-exact, where="post", color=GREEN if i == 4 else ORANGE, lw=2)
        lower.set(xlim=(2, 100), ylim=(-0.5, 4.1), xlabel="Cutoff x", ylabel="Extra count")
        lower.set_yticks([0, 2, 4])
        decorate(lower)
        fig.text(0.10, 0.125, formulas[i], fontsize=12)
        frames.append(capture(fig))
        plt.close(fig)
    return save_gif(frames, output_dir / "mobius_correction.gif", [2700]*4+[4300])


def build_zero_data() -> tuple[np.ndarray, dict[int, np.ndarray], np.ndarray, np.ndarray, dict]:
    """Evaluate actual zero sums and independently spot-check them with SciPy Ei."""
    heights = load_zero_heights(HERE / "data" / "odlyzko_zeros_10000.txt")
    regular = np.linspace(20.0, 40.0, 40001)
    checks = np.array([20.5, 23.0, 24.25, 28.999, 29.0, 29.001, 31.5, 37.0, 39.5])
    distances = np.geomspace(1e-7, 11.0, 12000)
    zoom = np.r_[29.0-distances, 29.0, 29.0+distances]
    zoom = zoom[(zoom >= 20) & (zoom <= 40)]
    dense = np.unique(np.r_[regular, zoom, checks])
    ordinary = np.unique(np.r_[regular, checks])
    direct = reconstruct_direct(checks, heights, COUNTS)
    curves, worst = {}, 0.0
    dense_values = None
    for count in COUNTS:
        grid = dense if count == 10000 else ordinary
        values, _ = reconstruct_fast(grid, heights[:count], threads=1)
        error = float(np.max(np.abs(values[np.searchsorted(grid, checks)] - direct[count])))
        assert error < 3e-7, (count, error)
        worst = max(worst, error)
        curves[count] = values[np.searchsorted(grid, regular)]
        if count == 10000:
            dense_values = values
    return regular, curves, dense, dense_values, {
        "maximum_direct_check_error": worst,
        "value_at_prime_29": float(direct[10000][4]),
        "direct_check_points": checks.tolist(),
        "zero_counts": list(COUNTS),
    }


def animate_zero_reconstruction(output_dir: Path, data: tuple) -> dict:
    x, curves, _, _, validation = data
    frames = []
    for i, count in enumerate(COUNTS):
        fig = new_figure(
            "Zeta zeros sharpen the prime staircase",
            "The same interval and scale at every stage; every blue curve is a computed finite sum.",
            "Zeros determine the blue curve. The sieve supplies only the dark comparison staircase.",
        )
        fig.text(0.10, 0.79, f"{count:,} zero pairs", fontsize=18, weight="bold", color=BLUE)
        fig.text(0.51, 0.79, f"{2*count:,} individual zeros in the sum", fontsize=12, color=MUTED)
        ax = fig.add_axes((0.10, 0.24, 0.85, 0.48))
        draw_exact(ax, 20, 40)
        ax.plot(x, curves[count], color=BLUE, lw=1.8, zorder=4,
                label="Explicit-formula reconstruction")
        ax.set(xlim=(20, 40), ylim=(7.5, 12.7), xlabel="Cutoff x", ylabel="Prime count")
        ax.set_xticks([20, 25, 30, 35, 40])
        ax.set_yticks([8, 9, 10, 11, 12])
        decorate(ax)
        ax.legend(loc="upper left", frameon=False, fontsize=10.5)
        if count == 0:
            detail = "0 pairs: smooth and trivial-zero corrections, with prime-power terms removed."
        elif count < 50:
            detail = "A few zero pairs add broad oscillations to the smooth starting curve."
        elif count < 1000:
            detail = "More zero pairs resolve individual steps; small ripples remain near each jump."
        else:
            detail = "The curves nearly overlap here. More zeros do not improve every point monotonically."
        fig.text(0.10, 0.14, detail, fontsize=11.1, color=MUTED)
        frames.append(capture(fig))
        plt.close(fig)
    durations = [1100] * len(frames)
    durations[0], durations[-1] = 1800, 3200
    result = save_gif(frames, output_dir / "zero_reconstruction.gif", durations)
    result["numerical_validation"] = validation
    return result


def animate_gibbs_zoom(output_dir: Path, data: tuple) -> dict:
    _, _, x, y, validation = data
    at29 = validation["value_at_prime_29"]
    frames = []
    for t in np.linspace(0.0, 1.0, 80):
        ease = t*t*(3-2*t)
        halfwidth = np.exp((1-ease)*np.log(10.0) + ease*np.log(0.03))
        # Keep prime 29 inside every window, not only at the final zoom.
        center = 29.0 + 0.1*halfwidth*(1-ease)
        xmin, xmax = center-halfwidth, center+halfwidth
        ymin, ymax = 7.5*(1-ease)+8.8*ease, 12.7*(1-ease)+10.2*ease
        fig = new_figure(
            "Zooming in reveals the remaining ripples",
            "10,000 zero pairs throughout: the calculation stays fixed while the viewing window narrows.",
            "At prime 29, the infinite zero sum returns the midpoint 9.5; the right-continuous count is 10.",
        )
        fig.text(0.10, 0.79, "10,000 pairs held fixed", fontsize=14, weight="bold", color=BLUE)
        fig.text(0.58, 0.79, f"Window width: {2*halfwidth:.4g}", fontsize=13, color=MUTED)
        ax = fig.add_axes((0.10, 0.24, 0.85, 0.48))
        draw_exact(ax, xmin, xmax)
        select = (x >= xmin) & (x <= xmax)
        ax.plot(x[select], y[select], color=BLUE, lw=1.6, zorder=4,
                label="10,000-pair reconstruction")
        ax.set(xlim=(xmin, xmax), ylim=(ymin, ymax), xlabel="Cutoff x", ylabel="Prime count")
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.xaxis.set_major_formatter(FormatStrFormatter("%.3f" if halfwidth < 0.2 else "%.1f" if halfwidth < 2 else "%.0f"))
        if halfwidth < 0.2:
            ax.set_xticks([29.0-2*halfwidth/3, 29.0, 29.0+2*halfwidth/3])
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
        decorate(ax)
        ax.legend(loc="upper left", frameon=False, fontsize=10.5)
        if halfwidth < 0.25:
            ax.axvline(29, color=MUTED, lw=0.8, alpha=0.4)
            ax.scatter([29], [at29], color=BLUE, s=35, zorder=5)
        fig.text(0.10, 0.14,
                 f"At x = 29: reconstruction = {at29:.5f}; midpoint = 9.5; exact prime count = 10.",
                 fontsize=11.4, color=MUTED)
        frames.append(capture(fig))
        plt.close(fig)
    durations = [140] * len(frames)
    durations[0], durations[-1] = 1500, 3500
    return save_gif(frames, output_dir / "gibbs_zoom.gif", durations)


def generate_all(output_dir: Path) -> list[dict]:
    output_dir = Path(output_dir)
    results = [animate_prime_powers(output_dir), animate_mobius_correction(output_dir)]
    data = build_zero_data()
    results.extend((animate_zero_reconstruction(output_dir, data), animate_gibbs_zoom(output_dir, data)))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE / "assets")
    parser.add_argument("--only", choices=NAMES, help="Regenerate one animation")
    args = parser.parse_args()
    if args.only is None:
        results = generate_all(args.output_dir)
    elif args.only == "prime_powers":
        results = [animate_prime_powers(args.output_dir)]
    elif args.only == "mobius_correction":
        results = [animate_mobius_correction(args.output_dir)]
    else:
        data = build_zero_data()
        fn = animate_zero_reconstruction if args.only == "zero_reconstruction" else animate_gibbs_zoom
        results = [fn(args.output_dir, data)]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
