#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy a signing asset to private storage and build a transparent PNG."
    )
    parser.add_argument("--source", required=True, help="Original source image path")
    parser.add_argument("--dest-dir", required=True, help="Private destination directory")
    parser.add_argument(
        "--name",
        required=True,
        help="Base name for generated files, for example your-stamp",
    )
    parser.add_argument(
        "--white-threshold",
        type=int,
        default=245,
        help="Treat RGB values at or above this threshold as near-white",
    )
    parser.add_argument(
        "--keep-threshold",
        type=int,
        default=12,
        help="How much non-white detail must remain before keeping a pixel opaque",
    )
    return parser.parse_args()


def white_to_alpha(
    source: Path,
    transparent_path: Path,
    white_threshold: int,
    keep_threshold: int,
) -> None:
    image = Image.open(source).convert("RGBA")
    out = []
    for r, g, b, a in image.getdata():
        keep = max(255 - r, 255 - g, 255 - b)
        if r >= white_threshold and g >= white_threshold and b >= white_threshold and keep < keep_threshold:
            out.append((r, g, b, 0))
        else:
            alpha = min(255, max(80, int((keep / 255) * 300)))
            out.append((r, g, b, alpha))

    image.putdata(out)
    bbox = image.getbbox()
    if bbox:
        image = image.crop(bbox)
    image.save(transparent_path)


def main() -> None:
    args = parse_args()
    source = Path(args.source).expanduser().resolve()
    dest_dir = Path(args.dest_dir).expanduser().resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_dir.chmod(0o700)

    original_copy = dest_dir / f"{args.name}_original{source.suffix.lower()}"
    transparent_copy = dest_dir / f"{args.name}_transparent.png"
    original_copy.write_bytes(source.read_bytes())
    white_to_alpha(
        original_copy,
        transparent_copy,
        white_threshold=args.white_threshold,
        keep_threshold=args.keep_threshold,
    )

    original_copy.chmod(0o600)
    transparent_copy.chmod(0o600)

    print(f"original={original_copy}")
    print(f"transparent={transparent_copy}")


if __name__ == "__main__":
    main()
