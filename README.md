# Image Resizer for OCR

Batch-resize images using the **`smart_resize`** algorithm, preserving aspect ratio and saving output as **PNG** for OCR pipelines.

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

# Verbose logging (includes Pillow debug output)
python resize_images.py -v
```

### CLI options

| Option | Default | Description |
|--------|---------|-------------|
| `-i`, `--input-dir` | `images` | Directory of source images |
| `-o`, `--output-dir` | `output` | Directory for output PNG files |
| `-v`, `--verbose` | off | Enable debug-level logging |

## Behavior

Every image in the input directory is processed with **`smart_resize`**:

| Parameter | Value |
|-----------|-------|
| `factor` | `28` |
| `min_pixels` | `640,000` |
| `max_pixels` | `2,822,400` |

The algorithm ensures:

1. **Dimension alignment** — height and width are divisible by `28`.
2. **Pixel budget** — total pixels stay within `[640,000, 2,822,400]`.
3. **Aspect ratio** — preserved as closely as possible.

| Input size | Typical action |
|------------|----------------|
| **&lt; 640k pixels** | Upscale until pixel count reaches the allowed range |
| **640k–2.82M pixels** | Adjust only if factor alignment changes dimensions |
| **&gt; 2.82M pixels** | Downscale until pixel count fits the allowed range |

Details:

- **Resampling** uses Pillow `LANCZOS` when dimensions change.
- **Aspect ratio guard** — images with an aspect ratio &gt; 200:1 are rejected with an error.
- **Color mode** is converted to RGB before saving.
- **Output format** is always PNG (`optimize=True`).
- **Output filename** is `{original_stem}.png` (extension replaced, not appended).
- **Unreadable files** (or extreme aspect ratios) are skipped with a warning; the script continues processing the rest.

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
INFO: Using smart_resize (factor=28, min_pixels=640000, max_pixels=2822400)
INFO: Upscaled cc.png: 716x1016 (0.73 MP) -> 1904x2688 (5.12 MP) -> output/cc.png
INFO: Downscaled visa-platinum.png: 5168x3344 (17.28 MP) -> 3920x2520 (9.88 MP) -> output/visa-platinum.png
INFO: Done. Resized 8 image(s), skipped 0.
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error (e.g. missing input directory) |
