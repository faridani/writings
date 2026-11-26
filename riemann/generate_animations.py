#!/usr/bin/env python3
"""Rebuild the article's animations or verify the existing GIF files.

Examples, from the repository root:
    python riemann/generate_animations.py
    python riemann/generate_animations.py --group reconstruction
    python riemann/generate_animations.py --verify-existing
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
GROUPS = {
    "primes": "animate_primes",
    "zeta": "animate_zeta",
    "reconstruction": "animate_reconstruction",
    "error": "animate_error_bound",
    "large-primes": "animate_large_primes",
}


def inspect_gifs(output_dir: Path) -> list[dict[str, object]]:
    results = []
    for path in sorted(output_dir.glob("*.gif")):
        with Image.open(path) as gif:
            size, count, loop = gif.size, gif.n_frames, gif.info.get("loop")
            duration = 0
            for index in range(count):
                gif.seek(index)
                gif.load()
                delay = gif.info.get("duration", 0)
                if delay <= 0:
                    raise ValueError(f"Missing or zero frame delay: {path}, frame {index}")
                duration += delay
            if count < 2 or loop != 0:
                raise ValueError(f"Expected a looping multi-frame GIF: {path}")
        results.append({
            "file": path.name, "dimensions": list(size), "frames": count,
            "duration_seconds": duration / 1000, "loop_forever": True,
            "size_bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    if not results:
        raise ValueError(f"No GIF files found in {output_dir}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE / "assets")
    parser.add_argument("--group", choices=["all", "sieve", *GROUPS], default="all")
    parser.add_argument("--verify-existing", action="store_true",
                        help="Decode and check existing GIFs without rebuilding them")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if not args.verify_existing:
        names = ["sieve", *GROUPS] if args.group == "all" else [args.group]
        for name in names:
            print(f"Building {name} animations...", flush=True)
            if name == "sieve":
                from generate_sieve_animation import save_animation
                result = save_animation(args.output_dir / "sieve_of_eratosthenes_1_to_100.gif")
            else:
                result = importlib.import_module(GROUPS[name]).generate_all(args.output_dir)
            print(json.dumps(result, indent=2), flush=True)
    manifest = {"animations": inspect_gifs(args.output_dir)}
    manifest["total_size_bytes"] = sum(item["size_bytes"] for item in manifest["animations"])
    manifest_path = (HERE if args.output_dir.resolve() == (HERE / "assets").resolve()
                     else args.output_dir) / "animation_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"manifest": str(manifest_path),
                      "animations": len(manifest["animations"]),
                      "total_size_bytes": manifest["total_size_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
