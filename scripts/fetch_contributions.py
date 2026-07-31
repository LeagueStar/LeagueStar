#!/usr/bin/env python3
"""
fetch_contributions.py

GitHub serves the profile contribution calendar as a public HTML fragment
at https://github.com/users/<username>/contributions - the same markup
the profile page itself uses. No GraphQL, no personal access token.

Usage:
    python scripts/fetch_contributions.py
Output:
    data/contributions.json
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "LeagueStar"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = Path(__file__).parent.parent / "data" / "contributions.json"

HEADERS = {
    # a normal browser UA avoids the odd bot-block on the contributions endpoint
    "User-Agent": "Mozilla/5.0 (compatible; profile-readme-bot/1.0)"
}


COUNT_RE = re.compile(r"^(no|\d+)\s+contributions?\s+on", re.IGNORECASE)


def build_tooltip_count_map(soup):
    """
    GitHub doesn't stamp a raw count onto each day cell - the number lives
    in a matching <tool-tip for="cell-id">N contributions on <date>.</tool-tip>
    element instead. Build id -> count from those.
    """
    counts = {}
    for tip in soup.find_all("tool-tip"):
        target_id = tip.get("for")
        text = tip.get_text(strip=True)
        m = COUNT_RE.match(text)
        if not target_id or not m:
            continue
        token = m.group(1).lower()
        counts[target_id] = 0 if token == "no" else int(token)
    return counts


def fetch_days():
    resp = requests.get(URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    count_map = build_tooltip_count_map(soup)

    days = []
    # GitHub renders each day as a <td> (older markup) or <rect> (svg calendar)
    # depending on rollout; handle both shapes defensively.
    cells = soup.select("td.ContributionCalendar-day") or soup.select("rect.ContributionCalendar-day")

    for cell in cells:
        d = cell.get("data-date")
        level = cell.get("data-level")
        cell_id = cell.get("id")

        if d is None:
            continue

        level = int(level) if level is not None else None
        count = count_map.get(cell_id)

        days.append({"date": d, "level": level, "count": count})

    days.sort(key=lambda x: x["date"])
    return days


def derive_stats(days):
    total = sum(d["count"] or 0 for d in days)

    # current streak: walk backward from the most recent day
    current_streak = 0
    for d in reversed(days):
        if (d["count"] or 0) > 0:
            current_streak += 1
        else:
            break

    # longest streak
    longest = 0
    running = 0
    for d in days:
        if (d["count"] or 0) > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0

    best_day = max(days, key=lambda d: d["count"] or 0, default=None)

    monthly = {}
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly[month_key] = monthly.get(month_key, 0) + (d["count"] or 0)

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest,
        "best_day": best_day,
        "monthly": monthly,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    days = fetch_days()
    if not days:
        raise SystemExit(
            "no contribution cells found - GitHub may have changed the "
            "markup on the /contributions endpoint. Check the selectors."
        )

    stats = derive_stats(days)
    payload = {"username": USERNAME, "days": days, "stats": stats}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"done -> {OUT} ({len(days)} days, {stats['total']} contributions)")


if __name__ == "__main__":
    main()
