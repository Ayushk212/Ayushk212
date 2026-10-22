# Setup — turning this into your live profile

## 1. Create the repo (must be named exactly your username)
```bash
gh repo create <your-username> --public --clone
# copy everything from this folder into it, or just push this folder there
```

## 2. Take and prep your photo
Read `README.md`'s comments / the notes below before shooting:
- side light at ~45°, everything else off
- crop tight: chin to just above hair, subject fills the frame
- 1200px+ resolution
- plain background, not black clothing on a dark wall
- slight angle, not dead-on

## 3. Build the font subsets (once)
```bash
pip install fonttools brotli
bash scripts/subset_font.sh
```
This downloads JetBrains Mono (OFL) and writes `fonts/ramp.woff2`,
`fonts/headings.woff2`, `fonts/basic.woff2`. Commit the LICENSE.txt
alongside it — required by the OFL.

## 4. Generate the portrait (once, or whenever you change photos)
```bash
pip install pillow numpy opencv-python-headless rembg onnxruntime
python3 scripts/ascii_portrait.py path/to/your-photo.jpg
```
First run downloads a ~176MB background-removal model (cached after).
Writes `portrait.svg`.

## 5. Generate the heading SVGs (once, or when you edit heading text)
Edit the `HEADINGS` list in `scripts/make_headings.py` to match your
own section titles, then:
```bash
python3 scripts/make_headings.py
```
Writes `headings/*.svg`, and update the `<img src="headings/...">`
paths in `README.md` to match.

## 6. Wire up the stats workflow
`.github/workflows/refresh.yml` automatically refreshes `scripts/generate_stats.py`
every 4 hours, and immediately whenever you push changes to `main` (ignoring the SVGs
themselves to prevent recursion). It commits `stats.svg` / `streak.svg` /
`langs.svg` / `year.svg` only when they actually change.

- **Public stats (default)**: Uses GitHub's built-in `GITHUB_TOKEN` automatically — no extra setup.
- **Include private/org contributions (334+ total)**: 
  1. Generate a Personal Access Token (classic) with `repo` and `read:user` scopes at **Settings > Developer Settings > Personal access tokens**.
  2. Add it as a repository secret named `PAT` under **Settings > Secrets and variables > Actions**.
  3. Ensure **"Include private contributions on my profile"** is checked in your GitHub **Settings > Public profile**.
  
You can also trigger it manually anytime from the Actions tab ("refresh stats" → Run workflow).

## 7. Force GitHub to pick it up
A newly created profile README is sometimes cached. If it doesn't
show on your profile page immediately, edit it once through the web
UI (even a trivial whitespace change) to force a refresh.

## Gotchas (from the guide, worth re-reading before you ship)
- Pinned repos and your bio can't be set via API — both are manual,
  in the profile UI.
- Test any markdown edits against `POST /markdown` before committing
  if you're unsure something will survive GitHub's sanitizer.
- Don't screenshot with `fullPage: true` in headless Chrome to verify
  the portrait — it restarts SMIL and you'll see a blank animation.
  Use a tall fixed viewport and wait ~5s for a full type-in.
