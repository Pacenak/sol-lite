#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
from pathlib import Path

import fitz
from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Place a transparent stamp or signature image onto a PDF page."
    )
    parser.add_argument("--input", required=True, help="Source PDF path")
    parser.add_argument("--output", required=True, help="Output PDF path")
    parser.add_argument("--image", required=True, help="Transparent asset path")
    parser.add_argument("--page", default="last", help='1-based page number or "last"')
    parser.add_argument("--x", type=float, required=True, help="Left X in PDF points")
    parser.add_argument("--y", type=float, required=True, help="Top Y in PDF points")
    parser.add_argument("--width", type=float, required=True, help="Placed width in PDF points")
    parser.add_argument("--opacity", type=float, default=1.0, help="Opacity 0..1")
    parser.add_argument(
        "--background",
        action="store_true",
        help="Place the asset below existing page content",
    )
    parser.add_argument("--preview", help="Optional PNG render path for the modified page")
    return parser.parse_args()


def resolve_page_index(doc: fitz.Document, page_arg: str) -> int:
    if page_arg == "last":
        return len(doc) - 1
    page_num = int(page_arg)
    if not 1 <= page_num <= len(doc):
        raise ValueError(f"Page {page_num} outside range 1..{len(doc)}")
    return page_num - 1


def build_image_stream(path: Path, opacity: float) -> tuple[bytes, int, int]:
    if not 0 < opacity <= 1:
        raise ValueError("Opacity must be between 0 and 1")

    img = Image.open(path).convert("RGBA")
    if opacity < 1:
        alpha = img.getchannel("A")
        alpha = alpha.point(lambda value: int(value * opacity))
        img.putalpha(alpha)

    width, height = img.size
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue(), width, height


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    image_path = Path(args.image).expanduser().resolve()
    preview_path = Path(args.preview).expanduser().resolve() if args.preview else None

    image_stream, image_width, image_height = build_image_stream(image_path, args.opacity)
    aspect = image_height / image_width
    placed_height = args.width * aspect

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if preview_path:
        preview_path.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(input_path)
    page_index = resolve_page_index(doc, args.page)
    page = doc[page_index]
    rect = fitz.Rect(args.x, args.y, args.x + args.width, args.y + placed_height)
    page.insert_image(
        rect,
        stream=image_stream,
        overlay=not args.background,
        keep_proportion=True,
    )
    doc.save(output_path, deflate=True, garbage=3)
    doc.close()

    if preview_path:
        preview_doc = fitz.open(output_path)
        preview_page = preview_doc[page_index]
        pix = preview_page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        pix.save(preview_path)
        preview_doc.close()

    print(f"output={output_path}")
    print(f"page_index={page_index}")
    print(f"placed_rect={tuple(rect)}")
    if preview_path:
        print(f"preview={preview_path}")


if __name__ == "__main__":
    main()
