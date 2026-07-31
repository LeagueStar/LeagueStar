#!/usr/bin/env python3
"""
render_heatmap_svg.py

Reads data/contributions.json and draws the classic 53-week x 7-day
calendar of rounded boxes. Boxes reveal once with a diagonal slide-down
(CSS keyframes that play on load, then freeze - no infinite looping
"glow"). Adds a Less -> More legend and a stats-footer line.

Usage:
    python scripts/render_heatmap_svg.py
Output:
    contrib-heatmap.svg   (repo root)
"""
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).parent.parent / "data" / "contributions.json"
OUT = Path(__file__).parent.parent / "contrib-heatmap.svg"

# none -> brightest (level 5 is a neon top end, GitHub only uses 0-4 but
# an extra top tier makes very high-activity days pop a bit more)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 12
GAP = 3
LEFT_PAD = 34   # room for day labels
TOP_PAD = 24    # room for month labels
FONT = "'SFMono-Regular',Consolas,'Liberation Mono',monospace"
BG = "#0d1117"
TEXT_MUTED = "#8b949e"
TEXT_MAIN = "#c9d1d9"

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_data():
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    return payload["days"], payload["stats"], payload.get("username", "")


def level_from_count(count, max_count):
    """Fall back to a count-based level if the scraper didn't get data-level."""
    if count is None or count == 0:
        return 0
    if max_count <= 0:
        return 1
    ratio = count / max_count
    if ratio > 0.85:
        return 5
    if ratio > 0.6:
        return 4
    if ratio > 0.35:
        return 3
    if ratio > 0.1:
        return 2
    return 1


def build_weeks(days):
    """Group days into columns (weeks) starting on Sunday, like GitHub's grid."""
    weeks = []
    current_week = [None] * 7
    max_count = max((d["count"] or 0) for d in days) if days else 0

    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        weekday = (dt.weekday() + 1) % 7  # convert Mon=0..Sun=6 -> Sun=0..Sat=6

        if weekday == 0 and any(c is not None for c in current_week):
            weeks.append(current_week)
            current_week = [None] * 7

        level = d["level"] if d.get("level") is not None else level_from_count(d["count"], max_count)
        current_week[weekday] = {"date": d["date"], "count": d["count"] or 0, "level": level}

    if any(c is not None for c in current_week):
        weeks.append(current_week)

    return weeks


def month_labels(weeks):
    """Emit a month label at the first week column where the month changes."""
    labels = []
    last_month = None
    for w_idx, week in enumerate(weeks):
        first_real = next((c for c in week if c is not None), None)
        if not first_real:
            continue
        month = int(first_real["date"][5:7])
        if month != last_month:
            labels.append((w_idx, MONTH_ABBR[month - 1]))
            last_month = month
    return labels


def main():
    days, stats, username = load_data()
    weeks = build_weeks(days)

    grid_w = len(weeks) * (CELL + GAP)
    grid_h = 7 * (CELL + GAP)
    width = LEFT_PAD + grid_w + 20
    height = TOP_PAD + grid_h + 70  # extra room for legend + footer text

    cells_svg = []
    delay_index = 0
    max_delay_steps = len(weeks) + 7  # diagonal stagger range

    for w_idx, week in enumerate(weeks):
        for d_idx, cell in enumerate(week):
            if cell is None:
                continue
            x = LEFT_PAD + w_idx * (CELL + GAP)
            y = TOP_PAD + d_idx * (CELL + GAP)
            color = PALETTE[min(cell["level"], len(PALETTE) - 1)]
            diag = w_idx + d_idx  # diagonal stagger key
            delay = round((diag / max_delay_steps) * 1.1, 3)

            cells_svg.append(
                f'<rect class="cell" x="{x}" y="{y - 6}" width="{CELL}" height="{CELL}" '
                f'rx="2.5" ry="2.5" fill="{color}" opacity="0" '
                f'style="animation-delay:{delay}s">'
                f'<title>{cell["count"]} contributions on {cell["date"]}</title>'
                f'</rect>'
            )

    labels_svg = []
    for w_idx, label in month_labels(weeks):
        x = LEFT_PAD + w_idx * (CELL + GAP)
        labels_svg.append(
            f'<text x="{x}" y="{TOP_PAD - 8}" font-family="{FONT}" font-size="10" '
            f'fill="{TEXT_MUTED}">{label}</text>'
        )

    day_labels = ["", "Mon", "", "Wed", "", "Fri", ""]
    day_labels_svg = []
    for i, lbl in enumerate(day_labels):
        if not lbl:
            continue
        y = TOP_PAD + i * (CELL + GAP) + CELL - 1
        day_labels_svg.append(
            f'<text x="4" y="{y}" font-family="{FONT}" font-size="9" '
            f'fill="{TEXT_MUTED}">{lbl}</text>'
        )

    legend_x = LEFT_PAD
    legend_y = TOP_PAD + grid_h + 30
    legend_svg = [f'<text x="{legend_x}" y="{legend_y + 9}" font-family="{FONT}" '
                  f'font-size="11" fill="{TEXT_MUTED}">Less</text>']
    lx = legend_x + 34
    for i, color in enumerate(PALETTE):
        legend_svg.append(
            f'<rect x="{lx + i * (CELL + GAP)}" y="{legend_y}" width="{CELL}" height="{CELL}" '
            f'rx="2.5" ry="2.5" fill="{color}" />'
        )
    legend_svg.append(
        f'<text x="{lx + len(PALETTE) * (CELL + GAP) + 6}" y="{legend_y + 9}" '
        f'font-family="{FONT}" font-size="11" fill="{TEXT_MUTED}">More</text>'
    )

    footer_y = legend_y + 26
    total = stats.get("total", 0)
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    footer_text = (
        f"{total:,} contributions in the last year   |   "
        f"current streak: {streak}   |   longest streak: {longest}"
    )
    footer_svg = (
        f'<text x="{LEFT_PAD}" y="{footer_y}" font-family="{FONT}" font-size="11" '
        f'fill="{TEXT_MAIN}">{footer_text}</text>'
    )

    style = f'''
  <style>
    .cell {{
      animation-name: reveal;
      animation-duration: 0.5s;
      animation-timing-function: cubic-bezier(.25,.1,.25,1);
      animation-fill-mode: forwards;
    }}
    @keyframes reveal {{
      from {{ opacity: 0; transform: translateY(-6px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}
  </style>'''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
     width="{width}" height="{height}">
  {style}
  <rect width="100%" height="100%" fill="{BG}" rx="8" ry="8" />
  {"".join(labels_svg)}
  {"".join(day_labels_svg)}
  {"".join(cells_svg)}
  {"".join(legend_svg)}
  {footer_svg}
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"done -> {OUT} ({len(weeks)} weeks, {total} contributions)")


if __name__ == "__main__":
    main()
