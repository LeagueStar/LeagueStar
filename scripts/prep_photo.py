#!/usr/bin/env python3
"""
prep_photo.py

Turns a normal photo into a clean, high-contrast grayscale image that is
ready to be converted into ASCII art. Run this once per photo, locally
(it needs rembg/opencv/numpy which are NOT part of the daily CI workflow).

Usage:
    python scripts/prep_photo.py source-photo.jpg
Output:
    scripts/source-prepped.png
"""
import sys
import io
from pathlib import Path

import numpy as np
from PIL import Image
import cv2
from rembg import remove

OUT_PATH = Path(__file__).parent / "source-prepped.png"


def remove_background(raw_bytes: bytes) -> Image.Image:
    """Isolate the subject on a transparent background."""
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
    if len(sys.argv) != 2:
        print("Usage: python prep_photo.py <source-photo.jpg>")
        sys.exit(1)

    src = Path(sys.argv[1])
    raw_bytes = src.read_bytes()

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
