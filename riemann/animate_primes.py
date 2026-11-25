#!/usr/bin/env python3
"""Rebuild the five elementary-number-theory animations in the article.

Run from the repository root:
    python riemann/animate_primes.py

All arithmetic and classifications are computed exactly. The RSA example
is deliberately tiny and omits the encoding/padding of a real RSA scheme.
"""

from __future__ import annotations

import argparse
import json
from math import gcd, isqrt, prod
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
import numpy as np

from animation_utils import (
    BLUE, GREEN, GRID, INK, MUTED, ORANGE, RED,
    capture, decorate, new_figure, save_gif,
)


HERE = Path(__file__).resolve().parent


def diagram_axes(fig: plt.Figure, bounds=(0.055, 0.17, 0.89, 0.60)):
    ax = fig.add_axes(bounds)
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    return ax


def box(ax, x, y, w, h, *, color=GRID, face="white", radius=0.02, lw=1.6):
    patch = FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad=0.008,rounding_size={radius}",
        facecolor=face, edgecolor=color, linewidth=lw,
    )
    ax.add_patch(patch)
    return patch


def factorization_routes(output_dir: Path) -> dict:
    """Show two exact binary factor trees ending in the same prime multiset."""
    routes = [
        ((0.23, 0.85, 60), [(0.12, 0.58, 6), (0.34, 0.58, 10)],
         [(0.06, 0.30, 2), (0.18, 0.30, 3), (0.28, 0.30, 2), (0.40, 0.30, 5)]),
        ((0.77, 0.85, 60), [(0.66, 0.58, 4), (0.88, 0.58, 15)],
         [(0.60, 0.30, 2), (0.72, 0.30, 2), (0.82, 0.30, 3), (0.94, 0.30, 5)]),
    ]
    assert all(prod(node[2] for node in r[2]) == 60 for r in routes)
    assert sorted(node[2] for node in routes[0][2]) == sorted(node[2] for node in routes[1][2])
    messages = [
        "Start with the same number",
        "Choose different first factors",
        "Split the composite factors into primes",
        "Reorder the leaves: the prime factors agree",
    ]
    frames, timings = [], []
    for stage in range(4):
        progress_values = [1.0] if stage in (0, 3) else np.linspace(0.15, 1, 7)
        for progress in progress_values:
            fig = new_figure(
                "Different routes, the same prime factors",
                "Unique factorization: 60 always breaks down into two 2s, one 3, and one 5.",
                "A factorization may be regrouped or reordered. The multiset of prime factors is unchanged.",
            )
            ax = diagram_axes(fig)
            ax.text(0.5, 1.065, messages[stage], ha="center", fontsize=14, weight="bold")
            ax.plot([0.50, 0.50], [0.22, 0.94], color=GRID, linewidth=1)
            for route, name in zip(routes, ("Route A: 6 × 10", "Route B: 4 × 15")):
                root, middle, leaves = route
                ax.text(root[0], 0.99, name, ha="center", fontsize=11, color=MUTED)

                def node(n, prime=False, alpha=1):
                    x, y, value = n
                    ax.add_patch(Circle((x, y), 0.046, facecolor="white",
                                        edgecolor=GREEN if prime else BLUE, linewidth=2.1, alpha=alpha))
                    ax.text(x, y, str(value), ha="center", va="center",
                            fontsize=21, weight="bold", color=GREEN if prime else INK, alpha=alpha)

                node(root)
                if stage >= 1:
                    alpha = float(progress) if stage == 1 else 1
                    for child in middle:
                        ax.plot([root[0], child[0]], [root[1] - 0.046, child[1] + 0.046],
                                color=BLUE, linewidth=1.8, alpha=alpha)
                        node(child, alpha=alpha)
                if stage >= 2:
                    alpha = float(progress) if stage == 2 else 1
                    for i, leaf in enumerate(leaves):
                        parent = middle[i // 2]
                        ax.plot([parent[0], leaf[0]], [parent[1] - 0.046, leaf[1] + 0.046],
                                color=GREEN, linewidth=1.8, alpha=alpha)
                        node(leaf, prime=True, alpha=alpha)
            if stage == 3:
                box(ax, 0.19, 0.035, 0.62, 0.115, color=GREEN, face="#f0f9f3")
                ax.text(0.50, 0.091, "60 = 2 × 2 × 3 × 5", ha="center", va="center",
                        fontsize=22, weight="bold", color=GREEN)
            frames.append(capture(fig))
            plt.close(fig)
            timings.append(90)
        timings[-1] = (1800, 2500, 2800, 3800)[stage]
    return save_gif(frames, output_dir / "factorization_routes.gif", timings)


def trial_division(output_dir: Path) -> dict:
    """Contrast a prime and a composite using exact integer quotients/remainders."""
    frames, timings = [], []
    states = list(range(2, 10)) + [None]
    for divisor in states:
        fig = new_figure(
            "A first prime test: stop at the square root",
            "Test 97 and 91 by dividing by 2, 3, …, 9. A zero remainder proves compositeness.",
            "If both factors exceeded √n, their product would exceed n. One factor must be at most √n.",
        )
        ax = diagram_axes(fig)
        for n, x in ((97, 0.025), (91, 0.535)):
            limit = isqrt(n)
            assert limit == 9
            found = n == 91 and (divisor is None or divisor >= 7)
            finished_prime = n == 97 and divisor is None
            color = RED if found else GREEN if finished_prime else BLUE
            box(ax, x, 0.16, 0.44, 0.81, color=color, face="#fbfcfe")
            ax.text(x + 0.22, 0.85, str(n), fontsize=36, weight="bold",
                    ha="center", color=color)
            ax.text(x + 0.22, 0.72, f"floor(√{n}) = {limit}", ha="center", fontsize=12, color=MUTED)
            active = 7 if found else 9 if divisor is None else divisor
            q, r = divmod(n, active)
            assert q * active + r == n
            ax.text(x + 0.22, 0.55, f"{n} = {q} × {active} + {r}", ha="center",
                    fontsize=19, weight="bold")
            message = ("Remainder 0: composite" if found else
                       "No divisor through 9: prime" if finished_prime else
                       f"Remainder {r}: try the next divisor")
            ax.text(x + 0.22, 0.42, message, ha="center", fontsize=11.5, color=color)
            for d in range(2, 10):
                dx = x + 0.035 + (d - 2) * 0.053
                tested = d <= active and (n != 91 or d <= 7)
                fill = RED if n == 91 and d == 7 and found else GREEN if tested else GRID
                ax.text(dx, 0.27, str(d), ha="center", va="center", fontsize=13,
                        weight="bold", color="white" if tested else MUTED,
                        bbox={"boxstyle": "round,pad=0.30", "facecolor": fill, "edgecolor": "none"})
        heading = "Both answers established" if divisor is None else f"Current divisor: {divisor}"
        ax.text(0.50, 0.04, heading, ha="center", fontsize=16, weight="bold", color=INK)
        frames.append(capture(fig))
        plt.close(fig)
        timings.append(1350 if divisor is not None else 3000)
    assert all(97 % d for d in range(2, isqrt(97) + 1)) and 91 % 7 == 0
    return save_gif(frames, output_dir / "trial_division.gif", timings)


def prime_count_staircase(output_dir: Path) -> dict:
    """Reveal the exact, right-continuous prime count for integer cutoffs 0..100."""
    primes = np.array([n for n in range(2, 101) if all(n % d for d in range(2, isqrt(n) + 1))])
    counts = np.searchsorted(primes, np.arange(101), side="right")
    assert len(primes) == 25 and counts[10] == 4 and counts[-1] == 25
    assert np.array_equal(np.flatnonzero(np.diff(counts)), primes - 1)
    frames, timings = [], []
    for n in range(101):
        count = int(counts[n])
        prime = n in primes
        fig = new_figure(
            "From finding primes to counting primes",
            "Move the cutoff x from 0 to 100. The count rises only when x reaches a prime.",
            "π(x) counts primes less than or equal to x. At x = 100, exactly 25 primes have been found.",
        )
        ax = fig.add_axes((0.10, 0.23, 0.83, 0.50))
        decorate(ax)
        ax.set(xlim=(0, 100), ylim=(0, 27), xlabel="Cutoff x", ylabel="Primes so far, π(x)")
        ax.set_xticks(np.arange(0, 101, 10))
        ax.set_yticks(np.arange(0, 26, 5))
        xs = np.arange(n + 1)
        ax.step(xs, counts[:n + 1], where="post", color=BLUE, linewidth=2.6)
        ax.axvline(n, color=GREEN if prime else BLUE, linewidth=1.0, alpha=0.35)
        ax.scatter([n], [count], s=48, color=GREEN if prime else BLUE, zorder=4, clip_on=False)
        if prime:
            ax.plot([n, n], [count - 1, count], color=GREEN, linewidth=4, solid_capstyle="round")
        for p in primes[primes <= n]:
            ax.plot([p, p], [0, 0.45], color=GREEN, linewidth=1, alpha=0.65)
        status = ("Before the first prime" if n < 2 else
                  f"{n} is prime: add one" if prime else f"{n} is composite: keep the count")
        fig.text(0.10, 0.785, status, fontsize=13, color=GREEN if prime else MUTED)
        fig.text(0.93, 0.785, f"π({n}) = {count}", ha="right", fontsize=19, weight="bold", color=INK)
        frames.append(capture(fig))
        plt.close(fig)
        timings.append(120)
    timings[0] = 800
    timings[-1] = 2600
    return save_gif(frames, output_dir / "prime_count_staircase.gif", timings)


def modular_arithmetic(output_dir: Path) -> dict:
    """Walk a seven-residue clock using exact addition and multiplication."""
    frames, timings = [], []
    states = [("addition", k) for k in range(5)]
    states += [("multiplication", k) for k in range(16)]
    for phase, step in states:
        total = 5 + step if phase == "addition" else step
        residue = total % 7
        fig = new_figure(
            "A prime can define the arithmetic",
            "Modulo 7, numbers wrap around the seven possible remainders: 0, 1, 2, 3, 4, 5, 6.",
            "Since 3 × 5 ≡ 1 (mod 7), multiplying by 5 undoes multiplication by 3.",
        )
        ax = fig.add_axes((0.045, 0.19, 0.45, 0.59))
        ax.set(xlim=(-1.25, 1.25), ylim=(-1.25, 1.25), aspect="equal")
        ax.axis("off")
        ax.add_patch(Circle((0, 0), 0.86, fill=False, edgecolor=GRID, linewidth=3))
        for r in range(7):
            angle = np.pi / 2 - 2 * np.pi * r / 7
            xx, yy = np.cos(angle), np.sin(angle)
            active = r == residue
            ax.add_patch(Circle((0.86 * xx, 0.86 * yy), 0.14, facecolor=GREEN if active else "white",
                                edgecolor=GREEN if active else GRID, linewidth=2))
            ax.text(0.86 * xx, 0.86 * yy, str(r), fontsize=20, weight="bold",
                    ha="center", va="center", color="white" if active else INK)
        start = 5 if phase == "addition" else 0
        if step:
            angles = np.linspace(np.pi / 2 - 2 * np.pi * start / 7,
                                 np.pi / 2 - 2 * np.pi * (start + step) / 7, 150)
            # Each completed wrap has the same clock positions; the status keeps the full total.
            ax.plot(0.60 * np.cos(angles), 0.60 * np.sin(angles), color=BLUE, linewidth=2.8, alpha=0.75)
            a = angles[-1]
            ax.plot([0, 0.65 * np.cos(a)], [0, 0.65 * np.sin(a)], color=GREEN, linewidth=2)
        ax.text(0, 0.1, str(residue), ha="center", fontsize=40, weight="bold", color=GREEN)
        ax.text(0, -0.22, "remainder", ha="center", fontsize=12, color=MUTED)
        tx = diagram_axes(fig, (0.54, 0.20, 0.40, 0.55))
        if phase == "addition":
            title = "Add four steps to 5"
            line1 = f"5 + {step} = {total}"
            line2 = f"{total} = {total // 7} × 7 + {residue}"
            conclusion = "5 + 4 ≡ 2 (mod 7)" if step == 4 else f"Step {step} of 4"
        else:
            title = "Multiply: three groups of 5"
            line1 = f"Running total: {total}"
            line2 = f"{total} = {total // 7} × 7 + {residue}"
            conclusion = ("3 × 5 ≡ 1 (mod 7)" if step == 15 else
                          f"Completed groups of 5: {step // 5}")
        tx.text(0, 0.87, title, fontsize=14, weight="bold")
        tx.text(0, 0.64, line1, fontsize=22, color=BLUE)
        tx.text(0, 0.43, line2, fontsize=18)
        tx.text(0, 0.20, conclusion, fontsize=16, weight="bold", color=GREEN)
        frames.append(capture(fig))
        plt.close(fig)
        timings.append(800 if phase == "addition" else 400)
        if step == 4 and phase == "addition":
            timings[-1] = 2200
        if step in (5, 10) and phase == "multiplication":
            timings[-1] = 900
        if step == 15 and phase == "multiplication":
            timings[-1] = 2800
    assert (5 + 4) % 7 == 2 and 3 * 5 % 7 == 1
    return save_gif(frames, output_dir / "modular_arithmetic.gif", timings)


def rsa_toy_example(output_dir: Path) -> dict:
    """Show the modular arithmetic of a tiny, explicitly insecure RSA example."""
    p, q, e, message = 61, 53, 17, 65
    modulus, phi = p * q, (p - 1) * (q - 1)
    d = pow(e, -1, phi)
    ciphertext = pow(message, e, modulus)
    recovered = pow(ciphertext, d, modulus)
    assert gcd(e, phi) == 1 and (modulus, phi, d, ciphertext, recovered) == (3233, 3120, 2753, 2790, 65)
    labels = [
        "1. Choose two secret primes",
        "2. Multiply them to form the modulus",
        "3. Count the invertible residues",
        "4. Choose a public exponent",
        "5. Compute the matching private exponent",
        "6. Encode a message as an integer",
        "7. Encrypt using the public key",
        "8. Decrypt using the private key",
        "The round trip recovers the original message",
    ]
    equations = [
        f"p = {p},     q = {q}",
        f"N = {p} × {q} = {modulus}",
        f"φ(N) = 60 × 52 = {phi}",
        f"e = {e},     gcd(17, 3120) = 1",
        f"d = {d},     17 × 2753 = 1 + 15 × 3120",
        f"m = {message},     0 ≤ m < {modulus}",
        f"c = 65¹⁷ mod 3233 = {ciphertext}",
        f"m = 2790²⁷⁵³ mod 3233 = {recovered}",
        "65 → 2790 → 65",
    ]
    frames, timings = [], []
    for stage in range(9):
        positions = np.linspace(0, 1, 9) if stage in (6, 7) else [1.0]
        for t in positions:
            fig = new_figure(
                "Toy RSA: primes create a reversible calculation",
                "Small numbers expose every step: choose factors first, then publish their product.",
                "Educational arithmetic only: these tiny keys are insecure; real RSA also uses secure encoding and padding.",
            )
            ax = diagram_axes(fig)
            ax.text(0.5, 1.01, labels[stage], ha="center", fontsize=14, weight="bold")
            box(ax, 0.025, 0.63, 0.44, 0.25, color=BLUE, face="#f3f7ff")
            box(ax, 0.535, 0.63, 0.44, 0.25, color=ORANGE, face="#fff8f1")
            ax.text(0.245, 0.82, "PUBLIC INFORMATION", fontsize=10.5, weight="bold", color=BLUE, ha="center")
            ax.text(0.755, 0.82, "SECRET INFORMATION", fontsize=10.5, weight="bold", color=ORANGE, ha="center")
            public = "Modulus not built yet" if stage == 0 else f"N = {modulus}" if stage < 3 else f"(e, N) = ({e}, {modulus})"
            secret = f"p = {p}, q = {q}" if stage < 4 else f"d = {d}; keep p and q secret"
            ax.text(0.245, 0.705, public, ha="center", fontsize=16 if stage >= 1 else 13)
            ax.text(0.755, 0.705, secret, ha="center", fontsize=14)
            ax.text(0.5, 0.46, equations[stage], ha="center", fontsize=20 if stage != 4 else 18,
                    weight="bold", color=GREEN if stage >= 7 else INK)
            if stage >= 5:
                centers = (0.15, 0.50, 0.85)
                texts = (str(message), str(ciphertext) if stage >= 6 else "?", str(recovered) if stage >= 7 else "?")
                tags = ("message m", "ciphertext c", "recovered m")
                for cx, text, tag in zip(centers, texts, tags):
                    box(ax, cx - 0.09, 0.11, 0.18, 0.17, color=GREEN if cx == 0.85 and stage >= 7 else GRID)
                    ax.text(cx, 0.195, text, ha="center", va="center", fontsize=22, weight="bold")
                    ax.text(cx, 0.04, tag, ha="center", fontsize=11, color=MUTED)
                for left, right, label in ((0.25, 0.40, "public key"), (0.60, 0.75, "private key")):
                    ax.add_patch(FancyArrowPatch((left, 0.195), (right, 0.195), arrowstyle="-|>",
                                                mutation_scale=15, color=BLUE, linewidth=1.8))
                    ax.text((left + right) / 2, 0.31, label, ha="center", fontsize=10, color=BLUE)
                if stage in (6, 7):
                    left, right = (0.25, 0.40) if stage == 6 else (0.60, 0.75)
                    ax.plot(left + float(t) * (right - left), 0.195, "o", color=GREEN, markersize=9, zorder=6)
            frames.append(capture(fig))
            plt.close(fig)
            timings.append(70)
        timings[-1] = 2500 if stage in (4, 6, 7) else 3000 if stage == 8 else 1600
    return save_gif(frames, output_dir / "rsa_toy_example.gif", timings)


ANIMATIONS = {
    "factorization_routes": factorization_routes,
    "trial_division": trial_division,
    "prime_count_staircase": prime_count_staircase,
    "modular_arithmetic": modular_arithmetic,
    "rsa_toy_example": rsa_toy_example,
}


def generate_all(output_dir: Path) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    return [generate(output_dir) for generate in ANIMATIONS.values()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE / "assets")
    parser.add_argument("--only", choices=list(ANIMATIONS))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metadata = ([ANIMATIONS[args.only](args.output_dir)] if args.only else generate_all(args.output_dir))
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
