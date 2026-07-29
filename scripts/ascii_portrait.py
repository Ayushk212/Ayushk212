#!/usr/bin/env python3
"""
Builds portrait.svg: a self-typing ASCII portrait, single fill colour,
font embedded as base64 woff2 so it renders identically everywhere
(GitHub strips <style>/class/inline-svg from README markdown, but an
<img>-loaded SVG file can carry its own @font-face + SMIL animation).

Usage:
    python3 scripts/ascii_portrait.py path/to/photo.jpg

Requirements (install once):
    pip install pillow numpy opencv-python-headless rembg onnxruntime

Photo requirements (see the guide):
  - side light (~45 deg), plain background, slight angle, not dead-on
  - tight crop: chin to just above hair, subject fills the frame
  - 1200px+ source resolution
"""
import base64
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

RAMP = " .`:-=+*cs#%@"          # dark->light... actually light(space) to dense
COLS = 90
CHAR_W = 7.74                    # em advance baked in at font-size 12.9, 0.600 em
FONT_SIZE = 12.9
FILL = "#e6edf3"
BG = "#0d1117"
STAGGER = 0.09                   # seconds between row starts
ROW_DUR = 0.5                    # seconds for a single row to type in


def load_and_cutout(path):
    with open(path, "rb") as f:
        raw = f.read()
    cut = remove(raw)  # RGBA, background made transparent
    img = Image.open(__import__("io").BytesIO(cut)).convert("RGBA")
    # composite onto white so background maps to the blank end of the ramp
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(bg, img).convert("RGB")
    return composited


def process(img):
    arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

    # bilateral filter: smooth skin, keep edges
    arr = cv2.bilateralFilter(arr, d=9, sigmaColor=75, sigmaSpace=75)

    # CLAHE: local contrast, clip ~3.0
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    arr = clahe.apply(arr)

    # darkening curve (v/255)^1.7 -- keeps glasses/brows/lips from washing out
    normalized = (arr.astype(np.float32) / 255.0) ** 1.7
    arr = (normalized * 255).astype(np.uint8)

    return arr


def to_ascii_rows(arr):
    h, w = arr.shape
    cols = COLS
    rows = max(1, int(cols * (h / w) * 0.48))
    resized = cv2.resize(arr, (cols, rows), interpolation=cv2.INTER_AREA)

    ramp_len = len(RAMP)
    rows_of_chars = []
    for r in range(rows):
        line = []
        for c in range(cols):
            v = resized[r, c]
            # brighter pixel -> further into blank end of ramp (index 0 = space)
            idx = int((255 - v) / 255 * (ramp_len - 1))
            line.append(RAMP[idx])
        rows_of_chars.append("".join(line))
    return rows_of_chars


def font_data_uri(woff2_path):
    data = Path(woff2_path).read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:font/woff2;base64,{b64}"


def build_svg(rows_of_chars, font_uri):
    cols = COLS
    rows = len(rows_of_chars)
    width = int(cols * CHAR_W) + 20
    row_h = FONT_SIZE * 1.0
    height = int(rows * row_h) + 20

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                  f'viewBox="0 0 {width} {height}">')
    parts.append(f'''<defs>
<style>
@font-face {{
  font-family: "PortraitRamp";
  src: url("{font_uri}") format("woff2");
}}
</style>
</defs>''')
    parts.append(f'<rect width="{width}" height="{height}" fill="{BG}" rx="6"/>')

    for i, line in enumerate(rows_of_chars):
        y = 10 + (i + 1) * row_h
        row_width = int(len(line) * CHAR_W)
        clip_id = f"clip{i}"
        begin = round(i * STAGGER, 3)
        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(f'  <rect x="10" y="{y - row_h}" width="0" height="{row_h + 4}">')
        parts.append(f'    <animate attributeName="width" from="0" to="{row_width}" '
                      f'begin="{begin}s" dur="{ROW_DUR}s" fill="freeze" '
                      f'calcMode="spline" keySplines="0.2 0 0.2 1"/>')
        parts.append('  </rect>')
        parts.append('</clipPath>')
        escaped = (line.replace("&", "&amp;").replace("<", "&lt;")
                       .replace(">", "&gt;"))
        parts.append(f'<text x="10" y="{y}" font-family="PortraitRamp, monospace" '
                      f'font-size="{FONT_SIZE}" fill="{FILL}" xml:space="preserve" '
                      f'clip-path="url(#{clip_id})">{escaped}</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def main():
    if len(sys.argv) < 2:
        print("usage: ascii_portrait.py path/to/photo.jpg [font.woff2]")
        sys.exit(1)
    photo_path = sys.argv[1]
    font_path = sys.argv[2] if len(sys.argv) > 2 else "fonts/ramp.woff2"

    img = load_and_cutout(photo_path)
    arr = process(img)
    rows_of_chars = to_ascii_rows(arr)
    font_uri = font_data_uri(font_path)
    svg = build_svg(rows_of_chars, font_uri)

    Path("portrait.svg").write_text(svg, encoding="utf-8")
    print(f"wrote portrait.svg  ({len(rows_of_chars)} rows x {COLS} cols)")


if __name__ == "__main__":
    main()
