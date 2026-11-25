"""Shared drawing and lossless frame-delta GIF export for the article.

All positions and curves are computed by the individual animation scripts.
Only the color palette is quantized to the GIF format's 256-color limit.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


INK = "#17283d"
BLUE = "#2166d6"
ORANGE = "#d77924"
GREEN = "#168746"
RED = "#cf4854"
PURPLE = "#8557c5"
MUTED = "#526174"
GRID = "#e4e9f0"
WIDTH, HEIGHT = 1000, 650


def setup_style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 12,
        "text.color": INK, "axes.labelcolor": INK,
        "axes.titlecolor": INK, "axes.titlesize": 13,
        "axes.titleweight": "bold", "axes.labelsize": 12,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "axes.facecolor": "white", "path.simplify": False,
    })


def new_figure(title: str, subtitle: str = "", footer: str = "") -> plt.Figure:
    """Return a 1000 x 650 canvas; axes belong inside y=0.17..0.78."""
    setup_style()
    fig = plt.figure(figsize=(10, 6.5), dpi=100)
    fig.text(0.055, 0.945, title, fontsize=22, weight="bold", va="top")
    if subtitle:
        fig.text(0.055, 0.878, subtitle, fontsize=12.4, color=MUTED, va="top")
    if footer:
        fig.text(0.055, 0.068, footer, fontsize=10.5, color=MUTED, va="top")
    return fig


def decorate(ax: plt.Axes) -> None:
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0, pad=6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#cad4df")


def capture(fig: plt.Figure) -> Image.Image:
    """Copy an Agg canvas so later artist updates cannot change saved frames."""
    fig.canvas.draw()
    return Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy())


def save_gif(
    frames: list[Image.Image], path: Path | str, durations: int | list[int] = 100,
) -> dict[str, object]:
    """Export a looping GIF with one shared palette and optimized deltas.

GIF timings are in 10 ms units. Identical neighboring frames may be merged
by Pillow; the actual saved total duration and final image are verified.
"""
    if not frames:
        raise ValueError("At least one frame is required.")
    size = frames[0].size
    if any(frame.size != size for frame in frames):
        raise ValueError("All animation frames must have the same size.")
    timing = [durations] * len(frames) if isinstance(durations, int) else list(durations)
    if len(timing) != len(frames) or any(t < 10 or t % 10 for t in timing):
        raise ValueError("Supply one positive multiple of 10 ms per frame.")

    sample_indices = np.unique(np.linspace(0, len(frames) - 1, min(6, len(frames)), dtype=int))
    atlas = Image.new("RGB", (size[0] * 2, size[1] * 3 + 50), "white")
    for tile, index in enumerate(sample_indices):
        atlas.paste(frames[index].convert("RGB"), ((tile % 2) * size[0], (tile // 2) * size[1]))
    # Keep even briefly used semantic colors in the common palette.
    from PIL import ImageDraw
    draw = ImageDraw.Draw(atlas)
    for i, color in enumerate((INK, BLUE, ORANGE, GREEN, RED, PURPLE, MUTED, GRID)):
        draw.rectangle((i * 100, size[1] * 3, (i + 1) * 100 - 1, size[1] * 3 + 49), fill=color)
    palette = atlas.quantize(colors=256, method=Image.Quantize.MEDIANCUT,
                             dither=Image.Dither.NONE)
    indexed = [frame.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE)
               for frame in frames]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    indexed[0].save(path, format="GIF", save_all=True, append_images=indexed[1:],
                    duration=timing, loop=0, disposal=1, optimize=True)

    with Image.open(path) as saved:
        actual_frames = saved.n_frames
        actual_duration = 0
        assert saved.size == size and saved.info.get("loop") == 0
        for index in range(actual_frames):
            saved.seek(index)
            actual_duration += saved.info.get("duration", 0)
        assert actual_duration == sum(timing), (path, actual_duration, sum(timing))
        assert np.array_equal(np.asarray(saved.convert("RGB")),
                              np.asarray(indexed[-1].convert("RGB"))), path
    return {
        "file": path.name, "dimensions": list(size), "frames": actual_frames,
        "duration_seconds": actual_duration / 1000,
        "size_bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
