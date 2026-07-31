#!/usr/bin/env python3
"""
make_info_card.py

Hand-authors a neofetch-style SVG panel: a title bar plus colored
key/value rows. Each line fades + slides in on a short stagger so it
looks like it's printing next to the ASCII portrait.

Set STATIC=1 to emit a frozen last-frame (handy for local Quick Look
previews where SMIL doesn't animate).

Usage:
    python scripts/make_info_card.py
Output:
    info-card.svg   (repo root)
"""
import os
from pathlib import Path

OUT = Path(__file__).parent.parent / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

WIDTH = 490
LINE_H = 26
PAD_X = 22
TITLE_H = 44
FONT = "'SFMono-Regular',Consolas,'Liberation Mono',monospace"

# --- edit this block to update the card's content ---
TITLE = "leaguestar@github"
FIELDS = [
    ("OS",     "B.Tech Information Technology"),
    ("Year",   "2nd Year"),
    ("Now",    "GCP + Terraform + Kubernetes"),
    ("Prev",   "1st Year - Cloud fundamentals"),
    ("Badges", "Compute Engine, VPC Networking, GKE"),
]
COLORS = {
    "key": "#39d353",
    "value": "#c9d1d9",
    "title_bg": "#161b22",
    "title_fg": "#79c0ff",
    "bg": "#0d1117",
    "border": "#30363d",
    "dot_red": "#ff5f56",
    "dot_yellow": "#ffbd2e",
    "dot_green": "#27c93f",
}
# ------------------------------------------------------

STAGGER = 0.16
FADE_DUR = 0.45


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def row_svg(i, key, value):
    y = TITLE_H + 34 + i * LINE_H
    key_x = PAD_X
    val_x = PAD_X + 130
    start = round(0.15 + i * STAGGER, 3)

    if STATIC:
        opacity_attr = 'opacity="1"'
        transform = ""
        anim = ""
    else:
        opacity_attr = 'opacity="0"'
        transform = f'transform="translate(-12,0)"'
        anim = f'''
        <animate attributeName="opacity" from="0" to="1" begin="{start}s" dur="{FADE_DUR}s" fill="freeze" />
        <animateTransform attributeName="transform" type="translate"
                           from="-12,0" to="0,0" begin="{start}s" dur="{FADE_DUR}s" fill="freeze" />'''

    return f'''
    <g {opacity_attr} {transform}>{anim}
      <text x="{key_x}" y="{y}" font-family="{FONT}" font-size="14" font-weight="600"
            fill="{COLORS['key']}" xml:space="preserve">{esc(key)}</text>
      <text x="{val_x}" y="{y}" font-family="{FONT}" font-size="14"
            fill="{COLORS['value']}" xml:space="preserve">{esc(value)}</text>
    </g>'''


def main():
    height = TITLE_H + 34 + len(FIELDS) * LINE_H + 20

    rows = "".join(row_svg(i, k, v) for i, (k, v) in enumerate(FIELDS))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}"
     width="{WIDTH}" height="{height}">
  <rect x="0" y="0" width="{WIDTH}" height="{height}" rx="10" ry="10"
        fill="{COLORS['bg']}" stroke="{COLORS['border']}" stroke-width="1" />

  <!-- title bar -->
  <rect x="0" y="0" width="{WIDTH}" height="{TITLE_H}" rx="10" ry="10" fill="{COLORS['title_bg']}" />
  <rect x="0" y="{TITLE_H - 10}" width="{WIDTH}" height="10" fill="{COLORS['title_bg']}" />
  <circle cx="24" cy="{TITLE_H/2}" r="6" fill="{COLORS['dot_red']}" />
  <circle cx="44" cy="{TITLE_H/2}" r="6" fill="{COLORS['dot_yellow']}" />
  <circle cx="64" cy="{TITLE_H/2}" r="6" fill="{COLORS['dot_green']}" />
  <text x="{WIDTH/2}" y="{TITLE_H/2 + 5}" text-anchor="middle" font-family="{FONT}"
        font-size="13" fill="{COLORS['title_fg']}">{esc(TITLE)}</text>

  <line x1="{PAD_X}" y1="{TITLE_H + 12}" x2="{WIDTH - PAD_X}" y2="{TITLE_H + 12}"
        stroke="{COLORS['border']}" stroke-width="1" />

  {rows}
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"done -> {OUT}")


if __name__ == "__main__":
    main()
