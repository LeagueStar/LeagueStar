#!/usr/bin/env python3
"""
make_ascii_svg.py

Downsamples the prepped photo (scripts/source-prepped.png) to a character
grid and maps brightness -> glyph density. Wraps each row in a clip-path
wipe so the portrait "types" itself in top to bottom when GitHub renders
the SVG (SMIL animation, no JS, no external CSS).

Usage:
    python scripts/make_ascii_svg.py
Output:
    avi-ascii.svg   (repo root)
"""
from pathlib import Path
from PIL import Image

SRC = Path(__file__).parent / "source-prepped.png"
OUT = Path(__file__).parent.parent / "avi-ascii.svg"

# bright (sparse) -> dark (dense). Leading space clears background to nothing.
RAMP = " .`:-=+*cs#%@"

COLS = 100
ROWS = 53
CHAR_W = 6.2
CHAR_H = 11
FONT_SIZE = 12
FILL = "#c9d1d9"          # single light-gray fill - monochrome on purpose
ROW_STAGGER = 0.035        # seconds between row starts
WIPE_DURATION = 0.6        # seconds per row wipe


def brightness_to_glyph(v: int) -> str:
    idx = int((1 - v / 255) * (len(RAMP) - 1))
    return RAMP[max(0, min(idx, len(RAMP) - 1))]


def image_to_ascii_rows(img: Image.Image, cols: int, rows: int):
    img = img.convert("L").resize((cols, rows))
    pixels = list(img.getdata())
    lines = []
    for r in range(rows):
        row_pixels = pixels[r * cols:(r + 1) * cols]
        line = "".join(brightness_to_glyph(p) for p in row_pixels)
        lines.append(line)
    return lines


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )


def build_svg(lines):
    width = COLS * CHAR_W
    height = ROWS * CHAR_H + 20

    defs = []
    rows_svg = []

    for i, line in enumerate(lines):
        y = 16 + i * CHAR_H
        clip_id = f"wipe{i}"
        start = round(i * ROW_STAGGER, 3)
        end = round(start + WIPE_DURATION, 3)

        # clip rect animates from width 0 -> full row width (left-to-right wipe)
        defs.append(f'''
    <clipPath id="{clip_id}">
      <rect x="0" y="{y - FONT_SIZE}" width="0" height="{FONT_SIZE + 4}">
        <animate attributeName="width" from="0" to="{width}"
                 begin="{start}s" dur="{WIPE_DURATION}s" fill="freeze"
                 calcMode="spline" keySplines="0.25 0.1 0.25 1" />
      </rect>
    </clipPath>''')

        # small block cursor that rides the wipe edge, then disappears
        cursor_x_attr = f"0;{width}"
        rows_svg.append(f'''
    <g clip-path="url(#{clip_id})">
      <text x="0" y="{y}" font-family="'SFMono-Regular',Consolas,'Liberation Mono',monospace"
            font-size="{FONT_SIZE}" fill="{FILL}" xml:space="preserve">{escape_xml(line)}</text>
    </g>
    <rect x="0" y="{y - FONT_SIZE}" width="2" height="{FONT_SIZE + 2}" fill="{FILL}" opacity="0">
      <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.01;0.9;1"
               begin="{start}s" dur="{WIPE_DURATION}s" fill="freeze" />
      <animate attributeName="x" from="0" to="{width}"
               begin="{start}s" dur="{WIPE_DURATION}s" fill="freeze"
               calcMode="spline" keySplines="0.25 0.1 0.25 1" />
    </rect>''')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
     width="{width}" height="{height}">
  <defs>{"".join(defs)}
  </defs>
  <rect width="100%" height="100%" fill="none" />
  {"".join(rows_svg)}
</svg>
'''
    return svg


def main():
    if not SRC.exists():
        print(f"missing {SRC} - run prep_photo.py first")
        raise SystemExit(1)

    img = Image.open(SRC)
    lines = image_to_ascii_rows(img, COLS, ROWS)
    svg = build_svg(lines)
    OUT.write_text(svg, encoding="utf-8")
    print(f"done -> {OUT}")


if __name__ == "__main__":
    main()
