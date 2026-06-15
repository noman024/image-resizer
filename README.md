# Image Resizer for OCR

Batch-resize images so every output file falls within a **5–10 megapixel (MP)** range, preserves aspect ratio, and is saved as **PNG** for OCR pipelines.

## Requirements

- Python 3.10+
- [Pillow](https://python-pillow.org/) ≥ 10.0.0

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
cd image-resizer
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

## Usage

Place source images in `images/` (or any directory you choose), then run:

```bash
python resize_images.py
```

Resized PNG files are written to `output/` by default.

### Examples

```bash
# Custom input/output directories
python resize_images.py -i ./photos -o ./resized

# Custom megapixel bounds
python resize_images.py --min-mp 5 --max-mp 10

# Verbose logging (includes Pillow debug output)
python resize_images.py -v
```

### CLI options

| Option | Default | Description |
|--------|---------|-------------|
| `-i`, `--input-dir` | `images` | Directory of source images |
| `-o`, `--output-dir` | `output` | Directory for output PNG files |
| `--min-mp` | `5.0` | Minimum output megapixels (inclusive) |
| `--max-mp` | `10.0` | Maximum output megapixels (inclusive) |
| `-v`, `--verbose` | off | Enable debug-level logging |

## Behavior

Megapixels are calculated as:

```
MP = (width × height) / 1,000,000
```

For **every** image in the input directory:

| Input size | Action |
|------------|--------|
| **&lt; 5 MP** | Upscale to ~10 MP |
| **5–10 MP** | Convert to PNG only (no resize) |
| **&gt; 10 MP** | Downscale to ~10 MP |

Details:

- **Aspect ratio** is always preserved.
- **Resampling** uses Pillow `LANCZOS` for upscale and downscale.
- **Rounding** adjusts width/height by ±1 px when needed so the final pixel count never exceeds `--max-mp` or falls below `--min-mp`.
- **Color mode** is converted to RGB before saving.
- **Output format** is always PNG (`optimize=True`).
- **Output filename** is `{original_stem}.png` (extension replaced, not appended).
- **Unreadable files** are skipped with a warning; the script continues processing the rest.

## Supported input formats

`.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tiff`, `.tif`, `.webp`, `.jfif`, `.pjpeg`, `.pjp`

Only files directly inside the input directory are processed (no subdirectories).

## Project layout

```
image-resizer/
├── images/           # default input directory
├── output/           # default output directory (created automatically)
├── resize_images.py  # main script
├── requirements.txt
├── .venv/            # virtual environment (local, not committed)
└── README.md
```

## Example log output

```
INFO: Input: /path/to/image-resizer/images
INFO: Output: /path/to/image-resizer/output
INFO: Resizing all images to output within 5.0–10.0 MP
INFO: Upscaled cc.png: 716x1016 (0.73 MP) -> 2655x3766 (10.00 MP) -> output/cc.png
INFO: Downscaled visa-platinum.png: 5168x3344 (17.28 MP) -> 3930x2544 (10.00 MP) -> output/visa-platinum.png
INFO: Done. Resized 8 image(s), skipped 0.
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error (missing input dir, invalid MP bounds, etc.) |
