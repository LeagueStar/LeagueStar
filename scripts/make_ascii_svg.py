#!/usr/bin/env python3
"""
make_ascii_svg.py

Downsamples the prepped image (scripts/source-prepped.png) to a character
grid and maps brightness -> glyph density. Wraps each row in a clip-path
wipe so the portrait "types" itself in top to bottom when GitHub renders
the SVG (SMIL animation, no JS, no external CSS).

After the reveal finishes, a small terminal cursor keeps blinking forever
at the bottom of the block. Without this, the whole thing plays once in
~2 seconds and then just sits there looking static - which is what makes
an SVG that IS animated feel "bland" to anyone who loads the page a few
seconds after it fired.

Usage:
    python scripts/make_ascii_svg.py                # normal photo (bright bg -> space)
    python scripts/make_ascii_svg.py --invert        # dark-bg art/avatars (dark bg -> space)
Output:
    <output-name>.svg   (repo root, default avi-ascii.svg)
"""
import argparse
from pathlib import Path
from PIL import Image

SRC = Path(__file__).parent / "source-prepped.png"

# bright (sparse) -> dark (dense) in normal mode.
RAMP = " .`:-=+*cs#%@"

COLS = 100
ROWS = 53
CHAR_W = 6.2
CHAR_H = 11
FONT_SIZE = 12
FILL = "#e6e0ff"           # single light fill - monochrome on purpose
ROW_STAGGER = 0.035         # seconds between row starts
WIPE_DURATION = 0.6         # seconds per row wipe
BG = "#0d1117"


def brightness_to_glyph(v: int, invert: bool) -> str:
    if invert:
        # bright (subject/content) -> dense, dark (background) -> space
        idx = int((v / 255) * (len(RAMP) - 1))
    else:
        # bright (background) -> space, dark (subject) -> dense
        idx = int((1 - v / 255) * (len(RAMP) - 1))
    return RAMP[max(0, min(idx, len(RAMP) - 1))]


def image_to_ascii_rows(img: Image.Image, cols: int, rows: int, invert: bool):
    img = img.convert("L").resize((cols, rows))
    pixels = list(img.getdata())
    lines = []
    for r in range(rows):
        row_pixels = pixels[r * cols:(r + 1) * cols]
        line = "".join(brightness_to_glyph(p, invert) for p in row_pixels)
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
    total_reveal_time = (len(lines) - 1) * ROW_STAGGER + WIPE_DURATION

    defs = []
    rows_svg = []

    for i, line in enumerate(lines):
        y = 16 + i * CHAR_H
        clip_id = f"wipe{i}"
        start = round(i * ROW_STAGGER, 3)

        defs.append(f'''
    <clipPath id="{clip_id}">
      <rect x="0" y="{y - FONT_SIZE}" width="0" height="{FONT_SIZE + 4}">
        <animate attributeName="width" from="0" to="{width}"
                 begin="{start}s" dur="{WIPE_DURATION}s" fill="freeze"
                 calcMode="spline" keySplines="0.25 0.1 0.25 1" />
      </rect>
    </clipPath>''')

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

    # persistent blinking cursor bottom-left, starts once the reveal
    # finishes and loops forever - this is what keeps the card feeling
    # "live" no matter when someone actually loads the profile page.
    cursor_y = height - 8
    cursor = f'''
  <rect x="0" y="{cursor_y - FONT_SIZE + 2}" width="7" height="{FONT_SIZE}" fill="{FILL}" opacity="0">
    <animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.001;0.5;0.501;1"
             begin="{round(total_reveal_time, 3)}s" dur="1.1s" repeatCount="indefinite" />
  </rect>'''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
     width="{width}" height="{height}">
  <rect width="100%" height="100%" fill="{BG}" />
  <defs>{"".join(defs)}
  </defs>
  {"".join(rows_svg)}
  {cursor}
</svg>
'''
    return svg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--invert", action="store_true",
                         help="use for dark-background art/avatars (see prep_photo.py --no-bg-removal)")
    parser.add_argument("--out", default=None, help="output filename (repo root)")
    args = parser.parse_args()

    if not SRC.exists():
        print(f"missing {SRC} - run prep_photo.py first")
        raise SystemExit(1)

    out_name = args.out or ("avi-ascii.svg")
    out_path = Path(__file__).parent.parent / out_name

    img = Image.open(SRC)
    lines = image_to_ascii_rows(img, COLS, ROWS, args.invert)
    svg = build_svg(lines)
    out_path.write_text(svg, encoding="utf-8")
    print(f"done -> {out_path}")


if __name__ == "__main__":
    main()
