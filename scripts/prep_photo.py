#!/usr/bin/env python3
"""
prep_photo.py

Turns a source image into a clean, high-contrast grayscale image that is
ready to be converted into ASCII art. Run this once per photo, locally
(it needs rembg/opencv/numpy which are NOT part of the daily CI workflow).

Two modes:
  - Normal photo (default): removes background, composites on white.
    Use this for a lit portrait photo where the subject should read as
    ink-on-paper (bright background -> blank space).
  - --no-bg-removal (for avatars, collages, stylized art that already
    sits on a flat dark background, e.g. a Discord/anime pfp): skips
    rembg and just boosts contrast. Pair with make_ascii_svg.py --invert
    so the dark background maps to blank space instead of the subject.

Usage:
    python scripts/prep_photo.py source-photo.jpg
    python scripts/prep_photo.py source-photo.jpg --no-bg-removal
Output:
    scripts/source-prepped.png
"""
import sys
import io
import argparse
from pathlib import Path

import numpy as np
from PIL import Image
import cv2

OUT_PATH = Path(__file__).parent / "source-prepped.png"


def remove_background(raw_bytes: bytes) -> Image.Image:
    """Isolate the subject on a transparent background."""
    from rembg import remove  # imported lazily - only needed in this path
    result = remove(raw_bytes)
    return Image.open(io.BytesIO(result)).convert("RGBA")


def boost_local_contrast(img: Image.Image) -> Image.Image:
    """
    CLAHE (contrast-limited adaptive histogram equalization).
    A flatly-lit face has almost no tonal range - CLAHE pulls real
    highlights and shadows out of it instead of a uniform gray blob.
    """
    rgb = img.convert("RGB")
    arr = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(arr)
    return Image.fromarray(enhanced).convert("L")


def composite_on_white(subject_rgba: Image.Image, gray: Image.Image) -> Image.Image:
    """
    Put the contrast-boosted subject back on a pure white canvas so the
    background maps to the blank end of the ASCII ramp (white -> space).
    """
    white_bg = Image.new("L", subject_rgba.size, 255)
    alpha = subject_rgba.split()[-1]
    white_bg.paste(gray, mask=alpha)
    return white_bg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--no-bg-removal", action="store_true",
                         help="skip rembg - use for avatars/art already on a flat dark background")
    args = parser.parse_args()

    src = Path(args.source)
    raw_bytes = src.read_bytes()

    if args.no_bg_removal:
        print("1/2  boosting local contrast (CLAHE)...")
        img = Image.open(io.BytesIO(raw_bytes))
        arr = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        final = Image.fromarray(clahe.apply(arr)).convert("L")
        print("2/2  saving (no background removal - pair with make_ascii_svg.py --invert)...")
    else:
        print("1/3  removing background...")
        subject = remove_background(raw_bytes)
        print("2/3  boosting local contrast (CLAHE)...")
        contrasted = boost_local_contrast(subject)
        print("3/3  compositing onto white...")
        final = composite_on_white(subject, contrasted)

    final.save(OUT_PATH)
    print(f"done -> {OUT_PATH}")


if __name__ == "__main__":
    main()
