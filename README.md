# Reading Digest

A weekly "issue" of 7 curated links on neuroscience, psychology, and
self-growth — sourced from Substack and Medium RSS feeds, filtered by an
AI curator against a written taste profile, and published as a small
journal/magazine-style static site.

## Status
- [x] Step 1 — Taste profile written (`TASTE_PROFILE.md`)
- [x] Step 2 — Feed aggregator (`scripts/fetch_candidates.py`) — pulls
      candidates from `config/feeds.yaml`, dedupes against `data/seen.json`
- [x] Step 3 — AI scoring layer (`scripts/score_candidates.py`) — scores
      each candidate against `TASTE_PROFILE.md`, writes top 7 to
      `data/picks.json` with a score, magazine-caption blurb, and tag
- [x] Step 4 — Issue data format (`scripts/generate_issue.py`) — wraps
      picks into a numbered issue, updates `data/issues/index.json` and
      `data/seen.json`
- [x] Step 5 — Static site (`scripts/build_site.py` + `templates/`) —
      journal/magazine design, renders `docs/index.html` +
      `docs/issues/issue-XXX.html` from the issue data
- [x] Step 6 — Weekly GitHub Actions automation
      (`.github/workflows/weekly.yml`) — runs every Monday, commits the
      new issue + rebuilt site automatically; also runnable on demand
- [ ] Step 7 — Deploy to GitHub Pages
- [ ] Step 8 — Star-rating feedback loop

## Project layout
```
reading-digest/
├── TASTE_PROFILE.md        # the spec the AI curator scores against
├── config/
│   └── feeds.yaml          # seed list of Substack pubs + Medium tags
├── data/
│   ├── seen.json           # links already used in a past issue (dedupe)
│   ├── candidates.json     # output of fetch_candidates.py
│   └── issues/             # generated issue files will land here (step 4)
├── scripts/
│   └── fetch_candidates.py # step 2, done
└── requirements.txt
```

## Running step 2 locally
```
pip install -r requirements.txt
python scripts/fetch_candidates.py
```
This writes `data/candidates.json` — the raw pool that step 3 will score.

Note: this needs real internet access to Substack/Medium, which wasn't
available in the sandbox this was built in — logic was verified against a
local sample feed instead. Should run as-is once you have it in your own
environment or GitHub Actions (which will have normal internet access).

## Running step 3 locally
```
export ANTHROPIC_API_KEY=sk-ant-...
python scripts/score_candidates.py
```
Reads `data/candidates.json`, scores each entry against `TASTE_PROFILE.md`,
and writes the top 7 (by score) to `data/picks.json`, each with a
`score`, `blurb` (magazine-caption style), and `tag`.

Note: like step 2, this wasn't live-tested end-to-end in the sandbox this
was built in (no API key available there) — the JSON-parsing logic was
unit-tested directly instead. Once you add your `ANTHROPIC_API_KEY`, this
should run as-is; if a request errors, it's most likely a real network/API
issue rather than a logic bug, worth checking the error message from the
`anthropic` client directly.

## Running steps 4 and 5 locally
```
python scripts/generate_issue.py
python scripts/build_site.py
```
`generate_issue.py` turns `data/picks.json` into a numbered issue file
under `data/issues/`, updates the issues index, and marks those links as
seen so they're never picked again. `build_site.py` renders everything in
`data/issues/` into `docs/index.html` and `docs/issues/issue-XXX.html`
using the templates in `templates/`. Both were tested end-to-end with
sample data — this is the part that's fully verified.

## Running the whole pipeline
Steps 2–5 in sequence, exactly what the weekly workflow (step 6) runs:
```
python scripts/fetch_candidates.py
python scripts/score_candidates.py   # needs ANTHROPIC_API_KEY set
python scripts/generate_issue.py
python scripts/build_site.py
```


## Deployment (step 7)
No extra script needed — `docs/` is already a normal static site.
GitHub Pages can serve it directly once you point it there in your repo
settings (exact steps below). Every time the weekly workflow commits a
new issue, the rebuilt `docs/` folder ships with it, so the live site
updates automatically — no separate deploy step to run.

## Setting this up in your own GitHub repo
1. Create a new repo on GitHub (public or private both work; private
   repos get free Actions minutes too).
2. From inside this `reading-digest/` folder:
   ```
   git init
   git add .
   git commit -m "Initial commit: reading digest pipeline"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```
3. Add your Anthropic API key as a repo secret (needed by step 3, the
   scoring script): on GitHub, go to **Settings → Secrets and variables →
   Actions → New repository secret**, name it `ANTHROPIC_API_KEY`, paste
   your key as the value.
4. Turn on GitHub Pages: **Settings → Pages** → under "Build and
   deployment", set Source to **Deploy from a branch**, branch **main**,
   folder **/docs** → Save. GitHub will give you a URL like
   `https://<your-username>.github.io/<repo-name>/`.
5. Do a first manual run so there's real content live instead of an
   empty site: go to the **Actions** tab → **Weekly reading digest** →
   **Run workflow**. Once it finishes (a minute or two), your Pages URL
   should show issue #1.
6. After that, it runs itself every Monday. You can always trigger it
   manually the same way if you want a new issue sooner, or add more
   feeds to `config/feeds.yaml` any time without touching any code.

## What's not built yet
Step 8 — a "loved this" star rating on each pick that feeds back into
the taste profile / scoring prompt over time. Worth doing once you've
seen a few real issues and have a feel for what the AI curator gets
right or wrong.
