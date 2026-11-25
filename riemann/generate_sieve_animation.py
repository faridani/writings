#!/usr/bin/env python3
"""Animate the sieve of Eratosthenes on the integers 1 through 100.

Run from any directory:
    python /path/to/riemann/generate_sieve_animation.py
    python /path/to/riemann/generate_sieve_animation.py --output /tmp/sieve.gif

The animation deliberately visits multiples from 2*p for every prime p,
including composites crossed out during earlier passes. This makes the
repeated work visible; an efficient sieve would start at p*p and stop its
crossing passes when p*p > 100. Each remaining prime is still circled.

Only Pillow and Matplotlib (for its bundled DejaVu fonts) are needed. No
network access, random numbers, or precomputed animation frames are used.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from math import isqrt
from pathlib import Path

from matplotlib import get_data_path
from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = HERE / "assets" / "sieve_of_eratosthenes_1_to_100.gif"
LIMIT = 100
WIDTH, HEIGHT, SCALE = 900, 1100, 2
GRID_X, GRID_Y, CELL = 70, 242, 76
INK = "#17283d"
MUTED = "#526174"
GRID = "#e2e7ed"
GREEN = "#21854c"
GREEN_FILL = "#edf8f0"
RED = "#cf4444"
GRAY = "#87929e"
GRAY_FILL = "#f0f2f5"
AMBER = "#d69520"
AMBER_FILL = "#fff3d3"


@dataclass(frozen=True)
class Frame:
    kind: str
    primes: frozenset[int]
    composites: frozenset[int]
    duration_ms: int
    number: int | None = None
    prime: int | None = None
    already_crossed: bool = False


def build_frames() -> list[Frame]:
    """Construct the exact event sequence and validate its mathematical state."""
    primes: set[int] = set()
    composites: set[int] = set()
    frames = [Frame("intro", frozenset(), frozenset(), 1200)]
    frames.append(Frame("one", frozenset(), frozenset(), 1800, number=1))

    for prime in range(2, LIMIT + 1):
        if prime in composites:
            continue
        primes.add(prime)
        frames.append(Frame("prime", frozenset(primes), frozenset(composites),
                            700, number=prime, prime=prime))
        for multiple in range(2 * prime, LIMIT + 1, prime):
            already_crossed = multiple in composites
            composites.add(multiple)
            frames.append(Frame("multiple", frozenset(primes),
                                frozenset(composites), 200, number=multiple,
                                prime=prime, already_crossed=already_crossed))

    frames.append(Frame("final", frozenset(primes), frozenset(composites), 4500))

    # Independent trial division checks that the final classification is exact.
    expected_primes = {
        n for n in range(2, LIMIT + 1)
        if all(n % d != 0 for d in range(2, isqrt(n) + 1))
    }
    assert primes == expected_primes and len(primes) == 25
    assert composites == set(range(2, LIMIT + 1)) - expected_primes
    assert len(composites) == 74 and primes.isdisjoint(composites)
    assert 1 not in primes | composites
    for prime in sorted(expected_primes):
        visits = [f.number for f in frames if f.kind == "multiple" and f.prime == prime]
        assert visits == list(range(2 * prime, LIMIT + 1, prime))
    assert [f.number for f in frames if f.kind == "prime"] == sorted(expected_primes)
    assert next(f for f in frames if f.prime == 3 and f.number == 6).already_crossed
    assert not next(f for f in frames if f.prime == 3 and f.number == 9).already_crossed

    previous_primes: frozenset[int] = frozenset()
    previous_composites: frozenset[int] = frozenset()
    for frame in frames:
        assert previous_primes <= frame.primes
        assert previous_composites <= frame.composites
        previous_primes, previous_composites = frame.primes, frame.composites
    return frames


def load_fonts() -> dict[str, ImageFont.FreeTypeFont]:
    folder = Path(get_data_path()) / "fonts" / "ttf"
    regular = folder / "DejaVuSans.ttf"
    bold = folder / "DejaVuSans-Bold.ttf"
    return {
        "title": ImageFont.truetype(str(bold), 34 * SCALE),
        "subtitle": ImageFont.truetype(str(regular), 22 * SCALE),
        "status": ImageFont.truetype(str(bold), 25 * SCALE),
        "detail": ImageFont.truetype(str(regular), 20 * SCALE),
        "number": ImageFont.truetype(str(regular), 28 * SCALE),
        "prime": ImageFont.truetype(str(bold), 28 * SCALE),
        "legend": ImageFont.truetype(str(regular), 18 * SCALE),
        "counter": ImageFont.truetype(str(regular), 18 * SCALE),
    }


def operation_text(frame: Frame) -> tuple[str, str]:
    if frame.kind == "intro":
        return "Start with the integers 1 to 100", "Circle primes; cross out their multiples, one at a time."
    if frame.kind == "one":
        return "1 is not prime", "Circle 1 in gray: it is neither prime nor composite."
    if frame.kind == "prime":
        p = frame.prime
        assert p is not None
        detail = (f"Start at 2 × {p} = {2*p}; visit every multiple up to 100."
                  if 2*p <= LIMIT
                  else f"2 × {p} = {2*p} > 100; there are no multiples in this grid.")
        return f"{p} is prime — circle it in green", detail
    if frame.kind == "multiple":
        p, n = frame.prime, frame.number
        assert p is not None and n is not None
        action = "already crossed; keep its X" if frame.already_crossed else "cross it out"
        return f"Visit the multiples of {p}", f"{p} × {n // p} = {n} — {action}."
    return "25 primes found", "74 composites crossed out; 1 is neither prime nor composite."


def render_frame(frame: Frame, fonts: dict[str, ImageFont.FreeTypeFont]) -> Image.Image:
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), "white")
    draw = ImageDraw.Draw(image)

    def box(coords: tuple[float, ...]) -> tuple[int, ...]:
        return tuple(round(c * SCALE) for c in coords)

    def text(x: float, y: float, value: str, font: str, fill: str = INK,
             anchor: str = "lt") -> None:
        draw.text((round(x * SCALE), round(y * SCALE)), value,
                  font=fonts[font], fill=fill, anchor=anchor)

    text(38, 32, "The sieve of Eratosthenes", "title")
    text(38, 79, "Find every prime from 1 to 100", "subtitle", MUTED)
    draw.rounded_rectangle(box((38, 122, 862, 218)), radius=13*SCALE,
                           fill="#f2f5f9")
    title, detail = operation_text(frame)
    text(58, 140, title, "status")
    text(58, 180, detail, "detail", MUTED)

    for n in range(1, LIMIT + 1):
        row, col = divmod(n - 1, 10)
        x, y = GRID_X + col * CELL, GRID_Y + row * CELL
        cx, cy = x + CELL / 2, y + CELL / 2
        draw.rectangle(box((x, y, x + CELL, y + CELL)), fill="white",
                       outline=GRID, width=SCALE)
        active = n == frame.number
        if active:
            draw.rounded_rectangle(box((x+3, y+3, x+CELL-3, y+CELL-3)),
                                   radius=9*SCALE, fill=AMBER_FILL,
                                   outline=AMBER, width=3*SCALE)

        is_prime = n in frame.primes
        is_composite = n in frame.composites
        if is_prime or (n == 1 and frame.kind != "intro"):
            color, fill = (GREEN, GREEN_FILL) if is_prime else (GRAY, GRAY_FILL)
            draw.ellipse(box((cx-29, cy-29, cx+29, cy+29)),
                         fill=fill, outline=color, width=3*SCALE)
        color = GREEN if is_prime else (MUTED if is_composite or n == 1 else INK)
        text(cx, cy-1, str(n), "prime" if is_prime else "number", color, "mm")
        if is_composite:
            draw.line(box((cx-23, cy-23, cx+23, cy+23)), fill=RED, width=3*SCALE)
            draw.line(box((cx-23, cy+23, cx+23, cy-23)), fill=RED, width=3*SCALE)

    # Stable symbols and labels keep gray 1 distinct from a green prime circle.
    legend_y = 1033
    draw.ellipse(box((74, legend_y-10, 94, legend_y+10)),
                 outline=GREEN, width=2*SCALE)
    text(105, legend_y, "Prime", "legend", anchor="lm")
    draw.line(box((222, legend_y-9, 240, legend_y+9)), fill=RED, width=2*SCALE)
    draw.line(box((222, legend_y+9, 240, legend_y-9)), fill=RED, width=2*SCALE)
    text(251, legend_y, "Composite", "legend", anchor="lm")
    draw.ellipse(box((420, legend_y-10, 440, legend_y+10)),
                 outline=GRAY, width=2*SCALE)
    text(451, legend_y, "1: neither", "legend", anchor="lm")
    draw.rounded_rectangle(box((650, legend_y-11, 672, legend_y+11)),
                           radius=4*SCALE, fill=AMBER_FILL,
                           outline=AMBER, width=2*SCALE)
    text(683, legend_y, "Active cell", "legend", anchor="lm")
    text(WIDTH/2, 1072,
         f"Prime circles: {len(frame.primes)}     •     Composite crosses: {len(frame.composites)}",
         "counter", MUTED, "mm")
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def save_animation(output: Path) -> dict[str, object]:
    frames = build_frames()
    fonts = load_fonts()

    # One shared palette preserves identical pixels across frames, so GIF delta
    # rectangles compress well without flickering colors or discarded markings.
    palette_sample = Image.new("RGB", (WIDTH * 2, HEIGHT))
    palette_sample.paste(render_frame(frames[-1], fonts), (0, 0))
    repeat_six = next(f for f in frames if f.prime == 3 and f.number == 6)
    palette_sample.paste(render_frame(repeat_six, fonts), (WIDTH, 0))
    palette = palette_sample.quantize(colors=256, method=Image.Quantize.MEDIANCUT,
                                     dither=Image.Dither.NONE)
    images = [render_frame(frame, fonts).quantize(palette=palette,
                                                 dither=Image.Dither.NONE)
              for frame in frames]
    durations = [frame.duration_ms for frame in frames]
    output.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(output, format="GIF", save_all=True, append_images=images[1:],
                   duration=durations, loop=0, disposal=1, optimize=True)

    # Verify the actual saved animation, not only the requested settings.
    with Image.open(output) as saved:
        assert saved.size == (WIDTH, HEIGHT)
        assert saved.info.get("loop") == 0
        assert saved.n_frames == len(frames)
        actual_durations = []
        for index in range(saved.n_frames):
            saved.seek(index)
            actual_durations.append(saved.info["duration"])
        assert actual_durations == durations

    multiples = [f for f in frames if f.kind == "multiple"]
    return {
        "output": str(output.resolve()),
        "dimensions": [WIDTH, HEIGHT],
        "frames": len(frames),
        "duration_seconds": sum(durations) / 1000,
        "prime_circles": len(frames[-1].primes),
        "composite_crosses": len(frames[-1].composites),
        "multiple_visits": len(multiples),
        "already_crossed_visits": sum(f.already_crossed for f in multiples),
        "size_bytes": output.stat().st_size,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="GIF destination (default: assets next to this script)")
    args = parser.parse_args()
    print(json.dumps(save_animation(args.output), indent=2))


if __name__ == "__main__":
    main()
