#!/usr/bin/env python3
"""
Generates stats.svg, streak.svg, langs.svg, year.svg from the GitHub GraphQL
API using only the Python standard library (no pip deps to break in CI).

Env vars:
  GITHUB_TOKEN  - provided automatically by Actions (secrets.GITHUB_TOKEN)
  GH_LOGIN      - the profile owner's username (github.repository_owner)
"""
import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

TOKEN = os.environ["GITHUB_TOKEN"]
LOGIN = os.environ["GH_LOGIN"]
API = "https://api.github.com/graphql"

# ---- palette / type, shared with the rest of the profile -----------------
BG = "#0d1117"
FG = "#e6edf3"
DIM = "#7d8590"
ACCENT = "#39d353"          # GitHub's own "high activity" green
RAMP = " .`:-=+*cs#%@"      # same ramp as the portrait
FONT_FAMILY = "JetBrains Mono, ui-monospace, monospace"

# ---- pin the window to whole UTC days (determinism trap #1) --------------
now = datetime.now(timezone.utc)
today_end = now.replace(hour=23, minute=59, second=59, microsecond=0)
window_start = (today_end - timedelta(days=364)).replace(hour=0, minute=0, second=0)
FROM = window_start.isoformat()
TO = today_end.isoformat()


def gql(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": LOGIN,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]


CONTRIB_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""

LANG_QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    repositories(first: 100, after: $after, privacy: PUBLIC, isFork: false,
                  ownerAffiliations: OWNER) {
      pageInfo { hasNextPage endCursor }
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def fetch_contributions():
    data = gql(CONTRIB_QUERY, {"login": LOGIN, "from": FROM, "to": TO})
    cal = data["user"]["contributionsCollection"]["contributionCalendar"]
    days = []
    for week in cal["weeks"]:
        for d in week["contributionDays"]:
            days.append((d["date"], d["contributionCount"]))
    return cal["totalContributions"], days


def fetch_languages():
    totals = {}
    after = None
    while True:
        data = gql(LANG_QUERY, {"login": LOGIN, "after": after})
        repos = data["user"]["repositories"]
        for repo in repos["nodes"]:
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                color = edge["node"]["color"] or "#8b949e"
                size = edge["size"]
                cur = totals.get(name, [0, color])
                cur[0] += size
                totals[name] = cur
        if not repos["pageInfo"]["hasNextPage"]:
            break
        after = repos["pageInfo"]["endCursor"]
    return totals


def streaks(days):
    cur = 0
    best = 0
    best_range = (None, None)
    cur_start = None
    run_start = None
    for date, count in days:
        if count > 0:
            if cur == 0:
                run_start = date
            cur += 1
            if cur > best:
                best = cur
                best_range = (run_start, date)
        else:
            cur = 0
    # trailing current streak (must include most recent day)
    cur = 0
    for date, count in reversed(days):
        if count > 0:
            cur += 1
        else:
            break
    cur_start = days[-cur][0] if cur else None
    return cur, (cur_start, days[-1][0] if cur else None), best, best_range


def svg_header(width, height):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT_FAMILY}">'
        f'<rect width="{width}" height="{height}" fill="{BG}" rx="6"/>'
    )


def text(x, y, s, size=13, fill=FG, weight="400", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" xml:space="preserve">{s}</text>')


def make_stats_svg(total, days):
    width, height = 460, 120
    weekly = []
    week = 0
    for i, (_, c) in enumerate(days):
        week += c
        if i % 7 == 6:
            weekly.append(week)
            week = 0
    weekly.append(week)
    weekly = weekly[-24:]
    maxw = max(weekly) or 1

    out = [svg_header(width, height)]
    out.append(text(20, 32, "contributions, last year", 11, DIM))
    out.append(text(20, 62, str(total), 34, FG, "700"))

    bar_w, gap = 8, 3
    base_y = 100
    chart_x = 200
    max_bar_h = 60
    for i, v in enumerate(weekly):
        h = 2 if maxw == 0 else max(2, int(v / maxw * max_bar_h))
        x = chart_x + i * (bar_w + gap)
        y = base_y - h
        out.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" '
                    f'fill="{ACCENT}" opacity="0.85" rx="1"/>')
    out.append('</svg>')
    return "".join(out)


def make_streak_svg(cur, cur_range, best, best_range):
    width, height = 460, 90
    out = [svg_header(width, height)]
    out.append(text(20, 30, "current streak", 11, DIM))
    out.append(text(20, 55, f"{cur}d", 26, ACCENT, "700"))
    if cur_range[0]:
        out.append(text(20, 74, f"{cur_range[0]} \u2192 {cur_range[1]}", 10, DIM))

    out.append(text(250, 30, "longest streak", 11, DIM))
    out.append(text(250, 55, f"{best}d", 26, FG, "700"))
    if best_range[0]:
        out.append(text(250, 74, f"{best_range[0]} \u2192 {best_range[1]}", 10, DIM))
    out.append('</svg>')
    return "".join(out)


def make_langs_svg(totals):
    width, height = 460, 150
    items = sorted(totals.items(), key=lambda kv: kv[1][0], reverse=True)[:6]
    grand = sum(v[0] for v in totals.values()) or 1

    out = [svg_header(width, height)]
    out.append(text(20, 26, "top languages, by bytes", 11, DIM))

    bar_x, bar_y, bar_w = 20, 40, 420
    x = bar_x
    for name, (size, color) in items:
        w = max(1, int(size / grand * bar_w))
        out.append(f'<rect x="{x}" y="{bar_y}" width="{w}" height="10" fill="{color}" rx="1"/>')
        x += w
    out.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" '
                f'fill="none" stroke="{DIM}" stroke-width="0.5" rx="1"/>')

    ly = bar_y + 34
    for i, (name, (size, color)) in enumerate(items):
        row = i // 2
        col = i % 2
        lx = bar_x + col * 220
        cy = ly + row * 20
        pct = size / grand * 100
        out.append(f'<circle cx="{lx+4}" cy="{cy-4}" r="4" fill="{color}"/>')
        out.append(text(lx + 16, cy, f"{name}  {pct:.1f}%", 11, FG))
    out.append('</svg>')
    return "".join(out)


def make_year_svg(days):
    width = 20 + 53 * 10
    height = 100
    out = [svg_header(width, height)]
    out.append(text(20, 20, "the year, one character per day", 11, DIM))

    max_c = max((c for _, c in days), default=1) or 1
    cols = {}
    for date, count in days:
        d = datetime.fromisoformat(date)
        week_idx = (d - datetime.fromisoformat(days[0][0])).days // 7
        dow = d.weekday()
        cols.setdefault(week_idx, {})[dow] = count

    cell = 10
    ox, oy = 20, 36
    for week_idx, rows in cols.items():
        for dow, count in rows.items():
            level = 0 if max_c == 0 else min(len(RAMP) - 1, int(count / max_c * (len(RAMP) - 1)))
            ch = RAMP[level] if count > 0 else " "
            x = ox + week_idx * cell
            y = oy + dow * cell
            out.append(text(x, y, ch, 11, ACCENT if count else DIM))
    out.append('</svg>')
    return "".join(out)


def write_if_changed(path, content):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            if f.read() == content:
                return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def main():
    total, days = fetch_contributions()
    totals = fetch_languages()
    cur, cur_range, best, best_range = streaks(days)

    write_if_changed("stats.svg", make_stats_svg(total, days))
    write_if_changed("streak.svg", make_streak_svg(cur, cur_range, best, best_range))
    write_if_changed("langs.svg", make_langs_svg(totals))
    write_if_changed("year.svg", make_year_svg(days))


if __name__ == "__main__":
    main()
