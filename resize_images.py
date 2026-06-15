#!/usr/bin/env python3
"""Resize any image so output is within 5–10 MP for OCR; save as PNG."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from PIL import Image

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".tiff",
    ".tif",
    ".webp",
    ".jfif",
    ".pjpeg",
    ".pjp",
}

DEFAULT_MIN_MP = 5.0
DEFAULT_MAX_MP = 10.0
MEGAPIXEL = 1_000_000


def megapixels(width: int, height: int) -> float:
    return (width * height) / MEGAPIXEL


def compute_resized_dimensions(
    width: int, height: int, target_mp: float, min_mp: float, max_mp: float
) -> tuple[int, int]:
    """Return dimensions at target_mp, clamped to [min_mp, max_mp] after rounding."""
    scale = (target_mp * MEGAPIXEL / (width * height)) ** 0.5
    new_width = max(1, round(width * scale))
    new_height = max(1, round(height * scale))

    while megapixels(new_width, new_height) > max_mp and (
        new_width > 1 or new_height > 1
    ):
        if new_width >= new_height:
            new_width -= 1
        else:
            new_height -= 1

    while megapixels(new_width, new_height) < min_mp:
        if new_width >= new_height:
            new_width += 1
        else:
            new_height += 1

    return new_width, new_height


def target_megapixels(current_mp: float, min_mp: float, max_mp: float) -> float | None:
    """
    Pick resize target so output falls within [min_mp, max_mp].

    Returns None when the image is already in range (convert-only).
    """
    if current_mp < min_mp:
        return max_mp
    if current_mp > max_mp:
        return max_mp
    return None


def is_image_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def process_image(
    input_path: Path,
    output_path: Path,
    min_mp: float,
    max_mp: float,
) -> tuple[int, int, int, int, float, float, str]:
    """
    Resize (or convert) a single image so output is within [min_mp, max_mp].

    Returns (old_w, old_h, new_w, new_h, old_mp, new_mp, action).
    """
    with Image.open(input_path) as image:
        image = image.convert("RGB")
        old_width, old_height = image.size
        old_mp = megapixels(old_width, old_height)
        target_mp = target_megapixels(old_mp, min_mp, max_mp)

        if target_mp is None:
            new_width, new_height = old_width, old_height
            action = "converted"
            output_image = image
        else:
            new_width, new_height = compute_resized_dimensions(
                old_width, old_height, target_mp, min_mp, max_mp
            )
            action = "upscaled" if target_mp > old_mp else "downscaled"
            output_image = image.resize(
                (new_width, new_height), Image.Resampling.LANCZOS
            )

        new_mp = megapixels(new_width, new_height)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_image.save(output_path, format="PNG", optimize=True)

    return old_width, old_height, new_width, new_height, old_mp, new_mp, action


def process_images(
    input_dir: Path,
    output_dir: Path,
    min_mp: float,
    max_mp: float,
) -> tuple[int, int]:
    """Process all images. Returns (processed_count, skipped_count)."""
    if min_mp >= max_mp:
        raise ValueError("min_mp must be less than max_mp")

    image_files = sorted(
        path for path in input_dir.iterdir() if is_image_file(path)
    )

    processed = 0
    skipped = 0

    for image_path in image_files:
        output_path = output_dir / f"{image_path.stem}.png"
        try:
            old_w, old_h, new_w, new_h, old_mp, new_mp, action = process_image(
                image_path, output_path, min_mp, max_mp
            )
        except Exception as exc:
            logging.warning("Skipping unreadable file %s: %s", image_path.name, exc)
            skipped += 1
            continue

        logging.info(
            "%s %s: %dx%d (%.2f MP) -> %dx%d (%.2f MP) -> %s",
            action.capitalize(),
            image_path.name,
            old_w,
            old_h,
            old_mp,
            new_w,
            new_h,
            new_mp,
            output_path,
        )
        processed += 1

    return processed, skipped


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Resize any image so output is within 5–10 MP for OCR. "
            "Aspect ratio is preserved; output is saved as PNG."
        )
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        type=Path,
        default=Path("images"),
        help="Directory containing source images (default: images)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for resized PNG files (default: output)",
    )
    parser.add_argument(
        "--min-mp",
        type=float,
        default=DEFAULT_MIN_MP,
        help=f"Minimum output megapixels (default: {DEFAULT_MIN_MP})",
    )
    parser.add_argument(
        "--max-mp",
        type=float,
        default=DEFAULT_MAX_MP,
        help=f"Maximum output megapixels (default: {DEFAULT_MAX_MP})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()

    if not input_dir.is_dir():
        logging.error("Input directory does not exist: %s", input_dir)
        return 1

    if args.min_mp <= 0 or args.max_mp <= 0:
        logging.error("min-mp and max-mp must be positive")
        return 1

    logging.info("Input: %s", input_dir)
    logging.info("Output: %s", output_dir)
    logging.info(
        "Resizing all images to output within %.1f–%.1f MP",
        args.min_mp,
        args.max_mp,
    )

    try:
        processed, skipped = process_images(
            input_dir=input_dir,
            output_dir=output_dir,
            min_mp=args.min_mp,
            max_mp=args.max_mp,
        )
    except ValueError as exc:
        logging.error("%s", exc)
        return 1

    logging.info("Done. Resized %d image(s), skipped %d.", processed, skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
