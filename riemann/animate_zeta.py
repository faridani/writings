#!/usr/bin/env python3
"""Rebuild five explanatory animations about Euler's product and zeta zeros.

The animation frames come from the displayed mathematical expressions.
The finite complex sum is explicitly an illustration, not an evaluation of
the analytically continued zeta function. The cosine animation likewise
shows a building block, not the complete prime-counting explicit formula.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
import numpy as np

from animation_utils import (
    BLUE, GREEN, GRID, INK, MUTED, ORANGE, PURPLE, RED,
    capture, decorate, new_figure, save_gif, setup_style,
)


HERE = Path(__file__).resolve().parent
PRIMES = np.array([2, 3, 5, 7, 11, 13, 17, 19, 23, 29])


def _smooth_integer(n: int, allowed_primes: np.ndarray) -> bool:
    """Whether all prime factors of n occur in the current finite product."""
    for p in allowed_primes:
        while n % int(p) == 0:
            n //= int(p)
    return n == 1


def euler_product(output_dir: Path) -> dict:
    fig = new_figure(
        "Euler's product: primes assemble the integers",
        r"At $s=2$, each new prime contributes the factor $1/(1-p^{-2})$.",
        "The grid shows only 1–60. Each product factor includes every power of its prime.",
    )
    grid = fig.add_axes((0.065, 0.265, 0.435, 0.435))
    grid.set(xlim=(0, 10), ylim=(0, 6))
    grid.axis("off")
    tiles, numbers = [], []
    for n in range(1, 61):
        col, row = (n - 1) % 10, 5 - (n - 1) // 10
        tile = Rectangle((col + 0.025, row + 0.025), .95, .95,
                         facecolor="#f5f7fa", edgecolor=GRID, linewidth=.9)
        grid.add_patch(tile)
        tiles.append(tile)
        numbers.append(grid.text(col + .5, row + .5, str(n), ha="center", va="center",
                                 fontsize=12.3, color=MUTED))
    fig.text(.065, .768, "Integers admitted by the included primes", fontsize=13, weight="bold")
    fig.text(.065, .215, "1 is always included: choose no prime powers.", fontsize=10.5, color=MUTED)

    ax = fig.add_axes((.605, .265, .335, .435))
    products = np.r_[1.0, np.cumprod(1 / (1 - PRIMES.astype(float) ** -2))]
    limit = np.pi**2 / 6
    assert np.all(np.diff(products) > 0) and products[-1] < limit
    ax.set(xlim=(-.2, 10.3), ylim=(.97, 1.71), xlabel="Primes included", ylabel="Product value")
    ax.set_xticks([0, 2, 4, 6, 8, 10])
    ax.set_yticks([1, 1.2, 1.4, 1.6])
    decorate(ax)
    ax.axhline(limit, color=ORANGE, linestyle="--", linewidth=1.5)
    ax.text(.2, limit + .028, r"$\zeta(2)=\pi^2/6\approx1.644934$", color=ORANGE, fontsize=10.7)
    curve, = ax.plot([], [], color=BLUE, linewidth=2.3, marker="o", markersize=5)
    stage = fig.text(.605, .768, "", fontsize=13, weight="bold")
    numeric = fig.text(.605, .155, "", fontsize=12, color=BLUE)
    progress = fig.text(.065, .155, "", fontsize=11, color=INK)
    frames, durations = [], []
    previous = np.zeros(60, dtype=bool)
    for k in range(len(PRIMES) + 1):
        admitted = np.array([_smooth_integer(n, PRIMES[:k]) for n in range(1, 61)])
        newly = admitted & ~previous
        if k == 0:
            assert admitted.sum() == 1 and admitted[0]
        curve.set_data(np.arange(k + 1), products[:k + 1])
        stage.set_text("No primes yet: empty product = 1" if k == 0 else f"Include prime {PRIMES[k - 1]}")
        numeric.set_text(f"Current product = {products[k]:.6f}")
        progress.set_text("Included primes: none" if k == 0 else "Included primes: " + ", ".join(map(str, PRIMES[:k])))
        for highlight in ([False] if k == 0 else [True, False]):
            for j, (tile, number) in enumerate(zip(tiles, numbers)):
                tile.set_facecolor("#fff1d7" if highlight and newly[j] else "#e5f2eb" if admitted[j] else "#f5f7fa")
                tile.set_edgecolor(ORANGE if highlight and newly[j] else GRID)
                number.set_color(GREEN if admitted[j] else MUTED)
                number.set_weight("bold" if admitted[j] else "normal")
            frames.append(capture(fig))
            durations.append(1200 if k == 0 else 700 if highlight else 1000)
        previous = admitted
    durations[-1] += 1400
    plt.close(fig)
    return save_gif(frames, output_dir / "euler_product.gif", durations)


def complex_rotation(output_dir: Path) -> dict:
    fig = new_figure(
        "Complex powers rotate and cancel",
        r"Fix $\sigma=1.5$ and increase $t$ in $s=\sigma+it$. Each arrow keeps its length.",
        "The right panel is an eight-term illustration in the convergent region, not the full zeta function.",
    )
    one = fig.add_axes((.075, .275, .34, .47))
    one.set(xlim=(-.43, .43), ylim=(-.43, .43), xlabel="Real part", ylabel="Imaginary part")
    one.set_aspect("equal")
    one.set_title(r"One rotating term: $2^{-s}$", loc="left", pad=17)
    one.set_xticks([-.3, 0, .3]); one.set_yticks([-.3, 0, .3])
    decorate(one)
    one.axhline(0, color=GRID, linewidth=1); one.axvline(0, color=GRID, linewidth=1)
    radius = 2 ** -1.5
    one.add_patch(Circle((0, 0), radius, fill=False, color=BLUE, alpha=.2, linewidth=1.5))
    arrow = FancyArrowPatch((0, 0), (radius, 0), arrowstyle="-|>", mutation_scale=18, color=BLUE, linewidth=2.4)
    one.add_patch(arrow)
    dot, = one.plot([radius], [0], "o", color=BLUE, markersize=6)

    chain = fig.add_axes((.555, .275, .385, .47))
    chain.set(xlim=(-.25, 2.05), ylim=(-.9, .9), xlabel="Real part", ylabel="Imaginary part")
    chain.set_aspect("equal")
    chain.set_title(r"$1^{-s}+2^{-s}+\cdots+8^{-s}$, head to tail", loc="left", pad=17)
    chain.set_xticks([0, .5, 1, 1.5, 2]); chain.set_yticks([-.5, 0, .5])
    decorate(chain)
    chain.axhline(0, color=GRID, linewidth=1); chain.axvline(0, color=GRID, linewidth=1)
    colors = [INK, BLUE, ORANGE, GREEN, PURPLE, BLUE, ORANGE, GREEN]
    vectors = []
    for color in colors:
        patch = FancyArrowPatch((0, 0), (0, 0), arrowstyle="-|>", mutation_scale=10,
                                color=color, linewidth=1.9)
        chain.add_patch(patch); vectors.append(patch)
    resultant = FancyArrowPatch((0, 0), (0, 0), arrowstyle="-|>", mutation_scale=17,
                               color=RED, linewidth=2.1, alpha=.8, linestyle="--")
    chain.add_patch(resultant)
    final_dot, = chain.plot([], [], "o", color=RED, markersize=5)
    clock = fig.text(.075, .145, "", fontsize=13, weight="bold")
    magnitude = fig.text(.555, .145, "", fontsize=12, color=RED)
    fig.text(.555, .105, "Colored arrows: terms. Dashed red arrow: their sum.", fontsize=10.3, color=MUTED)
    frames, durations = [], []
    n = np.arange(1, 9, dtype=float)
    for t in np.linspace(0, 18, 151):
        z = np.exp((-1.5 - 1j * t) * np.log(n))
        assert np.allclose(np.abs(z), n**-1.5, rtol=0, atol=1e-14)
        tip = z[1]
        arrow.set_positions((0, 0), (tip.real, tip.imag)); dot.set_data([tip.real], [tip.imag])
        points = np.r_[0 + 0j, np.cumsum(z)]
        for patch, start, end in zip(vectors, points[:-1], points[1:]):
            patch.set_positions((start.real, start.imag), (end.real, end.imag))
        end = points[-1]
        resultant.set_positions((0, 0), (end.real, end.imag)); final_dot.set_data([end.real], [end.imag])
        clock.set_text(fr"$t={t:5.2f}$     radius $2^{{-1.5}}={radius:.4f}$")
        magnitude.set_text(f"Magnitude of the eight-term sum: {abs(end):.4f}")
        frames.append(capture(fig)); durations.append(90)
    durations[0] += 900; durations[-1] += 1700
    plt.close(fig)
    return save_gif(frames, output_dir / "complex_rotation.gif", durations)


def analytic_continuation(output_dir: Path) -> dict:
    fig = new_figure(
        "A function can outlive its defining series",
        r"Compare the partial sums $S_N(z)=1+z+\cdots+z^N$ with the function $1/(1-z)$.",
        "At z = 2, the continued function is −1. The divergent series does not sum to −1.",
    )
    left = fig.add_axes((.08, .285, .375, .425))
    right = fig.add_axes((.575, .285, .365, .425))
    for ax in (left, right):
        ax.set(xlim=(-.2, 12.3), xlabel="Last power included, N")
        ax.set_xticks([0, 3, 6, 9, 12]); decorate(ax)
    left.set(ylim=(0, 2.25), ylabel="Partial sum")
    left.set_title(r"$z=1/2$: inside $|z|<1$", loc="left", pad=17)
    left.axhline(2, color=GREEN, linestyle="--", linewidth=1.5)
    left.text(.2, 2.07, "Continued function = 2", fontsize=11, color=GREEN)
    lcurve, = left.plot([], [], color=BLUE, linewidth=2.4, marker="o", markersize=5)
    right.set_yscale("symlog", base=2, linthresh=1)
    right.set(ylim=(-2, 16000), ylabel="Partial sum; signed log scale")
    right.set_yticks([-1, 0, 8, 64, 512, 4096])
    right.set_yticklabels(["−1", "0", "8", "64", "512", "4096"])
    right.set_title(r"$z=2$: outside $|z|<1$", loc="left", pad=17)
    right.axhline(-1, color=ORANGE, linestyle="--", linewidth=1.5)
    rcurve, = right.plot([], [], color=RED, linewidth=2.4, marker="o", markersize=5)
    left_value = fig.text(.08, .155, "", fontsize=12, color=BLUE)
    right_value = fig.text(.575, .155, "", fontsize=12, color=RED)
    fig.text(.575, .115, "Dashed line: continued value −1", fontsize=11, color=ORANGE)
    fig.text(.08, .115, "The partial sums approach 2.", fontsize=11, color=GREEN)
    exponents = np.arange(13)
    inside = np.cumsum(.5**exponents)
    outside = np.cumsum(2.0**exponents)
    assert np.allclose(inside, 2 - .5**exponents)
    assert np.array_equal(outside, 2.0**(exponents + 1) - 1)
    frames, durations = [], []
    for k in range(13):
        lcurve.set_data(exponents[:k + 1], inside[:k + 1])
        rcurve.set_data(exponents[:k + 1], outside[:k + 1])
        left_value.set_text(fr"$N={k:2d}$       $S_N(1/2)={inside[k]:.6f}$")
        right_value.set_text(fr"$N={k:2d}$       $S_N(2)={outside[k]:.0f}$")
        frames.append(capture(fig)); durations.append(1000)
    durations[-1] += 2200
    plt.close(fig)
    return save_gif(frames, output_dir / "analytic_continuation.gif", durations)


def zeta_zero_pairs(output_dir: Path) -> dict:
    heights = np.loadtxt(HERE / "data" / "odlyzko_zeros_10000.txt")[:10]
    assert np.all(np.diff(heights) > 0) and 14 < heights[0] < 15 and heights[-1] < 50
    fig = new_figure(
        "A zero and its conjugate form one pair",
        r"Place the first ten known pairs $\rho_n=1/2\pm i\gamma_n$ on the complex plane.",
        "These computed examples illustrate the statement; they do not prove it for every zero.",
    )
    table = fig.add_axes((.07, .245, .345, .505)); table.axis("off")
    table.text(0, 1, "Pair", weight="bold", fontsize=13, va="top")
    table.text(.27, 1, "Positive height γₙ", weight="bold", fontsize=13, va="top")
    rows = []
    for i in range(10):
        y = .89 - .082 * i
        rows.append((table.text(0, y, "", fontsize=13.5, va="center"),
                     table.text(.27, y, "", fontsize=13.5, va="center")))
    ax = fig.add_axes((.535, .245, .4, .505))
    ax.axvspan(0, 1, color=BLUE, alpha=.04)
    ax.axvline(.5, color=BLUE, linewidth=1.2, alpha=.6)
    ax.axhline(0, color=GRID, linewidth=1)
    ax.set(xlim=(-.07, 1.07), ylim=(-54, 54), xlabel="Real part", ylabel="Imaginary part")
    ax.set_xticks([0, .5, 1]); ax.set_yticks([-50, -25, 0, 25, 50])
    ax.set_title("Critical strip: 0 < real part < 1", loc="left", pad=15)
    decorate(ax)
    dots = ax.scatter([], [], s=35, color=BLUE, zorder=4)
    current = ax.scatter([], [], s=75, color=ORANGE, zorder=5)
    plus = ax.text(.57, 0, "", color=ORANGE, fontsize=11, va="center")
    minus = ax.text(.57, 0, "", color=ORANGE, fontsize=11, va="center")
    counter = fig.text(.07, .12, "", fontsize=15, weight="bold")
    fig.text(.535, .12, "Every shown point has real part 1/2.", fontsize=11.3, color=MUTED)
    frames, durations = [], []
    for k in range(11):
        for highlight in ([False] if k == 0 else [True, False]):
            vals = np.r_[heights[:k], -heights[:k]]
            dots.set_offsets(np.column_stack((np.full(len(vals), .5), vals)))
            current.set_offsets(np.array([[.5, heights[k - 1]], [.5, -heights[k - 1]]])
                                if highlight else np.empty((0, 2)))
            for i, (number, height) in enumerate(rows):
                number.set_text(str(i + 1) if i < k else "")
                height.set_text(f"{heights[i]:.9f}" if i < k else "")
                color = ORANGE if highlight and i == k - 1 else INK
                number.set_color(color); height.set_color(color)
            for label, sign in ((plus, 1), (minus, -1)):
                label.set_text(("+" if sign > 0 else "−") + f"{heights[k - 1]:.4f}" if highlight else "")
                label.set_y(sign * heights[k - 1] if k else 0)
            counter.set_text(f"{k} pair{'s' if k != 1 else ''} = {2 * k} zeros")
            frames.append(capture(fig)); durations.append(1000 if k == 0 else 800 if highlight else 900)
    durations[-1] += 1800
    plt.close(fig)
    return save_gif(frames, output_dir / "zeta_zero_pairs.gif", durations)


def conjugate_waves(output_dir: Path) -> dict:
    heights = np.loadtxt(HERE / "data" / "odlyzko_zeros_10000.txt")[:3]
    fig = new_figure(
        "Conjugate pairs create real oscillations",
        r"After dividing out the amplitude: $(x^\rho+x^{\bar\rho})/(2\sqrt{x})=\cos(\gamma\log x)$.",
        "This cosine is a building block; the full reconstruction also needs Ei terms and prime-power corrections.",
    )
    phasor = fig.add_axes((.075, .29, .30, .405))
    phasor.set(xlim=(-1.2, 1.2), ylim=(-1.2, 1.2), xlabel="Real part", ylabel="Imaginary part")
    phasor.set_aspect("equal"); phasor.set_xticks([-1, 0, 1]); phasor.set_yticks([-1, 0, 1])
    decorate(phasor)
    phasor.axhline(0, color=GRID, linewidth=1); phasor.axvline(0, color=GRID, linewidth=1)
    phasor.add_patch(Circle((0, 0), 1, fill=False, color=MUTED, alpha=.2))
    phasor.set_title("Normalized conjugate vectors", loc="left", pad=22)
    a = FancyArrowPatch((0, 0), (1, 0), arrowstyle="-|>", mutation_scale=16, color=BLUE, linewidth=2)
    b = FancyArrowPatch((0, 0), (1, 0), arrowstyle="-|>", mutation_scale=16, color=ORANGE, linewidth=2)
    phasor.add_patch(a); phasor.add_patch(b)
    projection, = phasor.plot([0, 1], [0, 0], color=GREEN, linewidth=3.2)
    projection_dot, = phasor.plot([1], [0], "o", color=GREEN, markersize=5)
    wave = fig.add_axes((.495, .29, .445, .405))
    wave.set(xlim=(0, 1), ylim=(-1.2, 1.2), xlabel=r"$\log x$", ylabel="Normalized real contribution")
    wave.set_xticks([0, .25, .5, .75, 1]); wave.set_yticks([-1, 0, 1]); decorate(wave)
    wave.axhline(0, color=GRID, linewidth=1)
    ugrid = np.linspace(0, 1, 700)
    future, = wave.plot([], [], color=GRID, linewidth=1.5)
    trace, = wave.plot([], [], color=GREEN, linewidth=2.4)
    cursor = wave.axvline(0, color=GREEN, alpha=.3, linewidth=1)
    moving, = wave.plot([], [], "o", color=GREEN, markersize=6)
    pair_label = fig.text(.495, .765, "", fontsize=13, weight="bold")
    phase_label = fig.text(.495, .13, "", fontsize=11.8, color=MUTED)
    fig.text(.075, .13, "Imaginary parts cancel.\nThe common real part remains.", fontsize=11, color=MUTED)
    frames, durations = [], []
    for pair, gamma in enumerate(heights, 1):
        pair_label.set_text(f"Pair {pair}: γ = {gamma:.6f}")
        all_y = np.cos(gamma * ugrid)
        future.set_data(ugrid, all_y)
        for u in np.linspace(0, 1, 61):
            theta = gamma * u
            z = np.exp(1j * theta)
            x = np.exp(u)
            real_sum = x**(.5 + 1j * gamma) + x**(.5 - 1j * gamma)
            assert abs(real_sum.imag) < 1e-14
            assert abs(real_sum.real / (2 * np.sqrt(x)) - np.cos(theta)) < 1e-13
            a.set_positions((0, 0), (z.real, z.imag)); b.set_positions((0, 0), (z.real, -z.imag))
            projection.set_data([0, z.real], [0, 0]); projection_dot.set_data([z.real], [0])
            selected = ugrid <= u
            trace.set_data(np.r_[ugrid[selected], u], np.r_[all_y[selected], np.cos(theta)])
            cursor.set_xdata([u, u]); moving.set_data([u], [np.cos(theta)])
            phase_label.set_text(f"log x = {u:.3f}     x = {x:.3f}     real part = {z.real:+.3f}")
            frames.append(capture(fig)); durations.append(80)
        durations[-1] += 1000
    durations[0] += 800; durations[-1] += 1200
    plt.close(fig)
    return save_gif(frames, output_dir / "conjugate_waves.gif", durations)


GENERATORS = {
    "euler_product": euler_product,
    "complex_rotation": complex_rotation,
    "analytic_continuation": analytic_continuation,
    "zeta_zero_pairs": zeta_zero_pairs,
    "conjugate_waves": conjugate_waves,
}


def generate_all(output_dir: Path) -> list[dict]:
    setup_style()
    return [generator(Path(output_dir)) for generator in GENERATORS.values()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE / "assets")
    parser.add_argument("--only", choices=GENERATORS)
    args = parser.parse_args()
    results = ([GENERATORS[args.only](args.output_dir)] if args.only else generate_all(args.output_dir))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
