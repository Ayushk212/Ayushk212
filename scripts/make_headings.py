#!/usr/bin/env python3
"""
Generates one small SVG per section heading: lowercase mono label + a
hairline rule running to the right edge. This is the only way to put your
own typeface on a heading, since GitHub strips <style>, class, and inline
<svg> from README markdown -- but an <img>-loaded SVG file is unaffected.

Usage:
    python3 scripts/make_headings.py

Edit HEADINGS below to match your README's section titles.
"""
import base64
from pathlib import Path

HEADINGS = [
    "why not just use the usual cards",
    "what github actually allows",
    "part 1 — the portrait",
    "part 2 — stats your own repo draws",
    "part 3 — making the text look deliberate",
]

WIDTH = 640
HEIGHT = 34
FONT_SIZE = 15
FILL = "#e6edf3"
RULE = "#30363d"
FONT_PATH = "fonts/headings.woff2"


def font_uri():
    data = Path(FONT_PATH).read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:font/woff2;base64,{b64}"


def slug(s):
    return "".join(c if c.isalnum() else "-" for c in s.lower()).strip("-")


def build(heading, uri):
    escaped = (heading.replace("&", "&amp;").replace("<", "&lt;")
                       .replace(">", "&gt;"))
    text_w = len(heading) * FONT_SIZE * 0.62  # rough advance for rule start
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}"
     viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{escaped}">
  <defs>
    <style>
      @font-face {{
        font-family: "HeadingMono";
        src: url("{uri}") format("woff2");
      }}
    </style>
  </defs>
  <text x="0" y="22" font-family="HeadingMono, monospace" font-size="{FONT_SIZE}"
        fill="{FILL}" xml:space="preserve">{escaped}</text>
  <line x1="{text_w + 14}" y1="17" x2="{WIDTH}" y2="17" stroke="{RULE}" stroke-width="1"/>
</svg>'''


def main():
    uri = font_uri()
    Path("headings").mkdir(exist_ok=True)
    for h in HEADINGS:
        out = Path("headings") / f"{slug(h)}.svg"
        out.write_text(build(h, uri), encoding="utf-8")
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
