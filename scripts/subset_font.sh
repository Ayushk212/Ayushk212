#!/usr/bin/env bash
# Downloads JetBrains Mono (OFL) and subsets it into the three small woff2
# files the guide uses, instead of inlining a ~4.5MB TTF into every SVG.
#
#   ramp.woff2      - the 13 ramp characters used by the portrait
#   headings.woff2  - only the letters actually used in section headings
#   basic.woff2     - basic latin, for the stats/data graphics
#
# Requires: pip install fonttools brotli
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p fonts
cd fonts

if [ ! -f JetBrainsMono-Regular.ttf ]; then
  curl -sL -o JetBrainsMono.zip \
    "https://github.com/JetBrains/JetBrainsMono/releases/latest/download/JetBrainsMono-2.304.zip"
  unzip -o -q JetBrainsMono.zip -d _jbm
  cp _jbm/fonts/ttf/JetBrainsMono-Regular.ttf .
  cp _jbm/OFL.txt LICENSE.txt
  rm -rf _jbm JetBrainsMono.zip
fi

# 1) ramp subset — just the 13 characters the portrait draws with
# (note: --layout-features='' with an empty value trips fontTools' own
#  option parser and swallows the following args — omit it instead)
pyftsubset JetBrainsMono-Regular.ttf --text=' .`:-=+*cs#%@' \
  --flavor=woff2 --no-hinting --output-file=ramp.woff2

# 2) headings subset — letters used across section headings (edit the
#    --text string below if you change your heading wording)
HEADINGS_TEXT="abcdefghijklmnopqrstuvwxyz0123456789 —-.,:/'"
pyftsubset JetBrainsMono-Regular.ttf --text="$HEADINGS_TEXT" \
  --flavor=woff2 --no-hinting --output-file=headings.woff2

# 3) basic latin, regular + bold — for the data graphics
pyftsubset JetBrainsMono-Regular.ttf --unicodes="U+0020-007E" \
  --flavor=woff2 --no-hinting --output-file=basic.woff2

echo "wrote fonts/ramp.woff2, fonts/headings.woff2, fonts/basic.woff2"
ls -la *.woff2
