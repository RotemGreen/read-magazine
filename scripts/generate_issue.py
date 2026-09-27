"""
Step 4 — Issue generation.

Reads data/picks.json (from score_candidates.py), wraps it into a numbered
"issue" with a date, writes it to data/issues/issue-XXX.json, updates
data/issues/index.json (the list the site reads to know what issues
exist), and adds this issue's links to data/seen.json so they're never
picked again.

Usage:
    python scripts/generate_issue.py
"""

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PICKS_PATH = ROOT / "data" / "picks.json"
ISSUES_DIR = ROOT / "data" / "issues"
INDEX_PATH = ISSUES_DIR / "index.json"
SEEN_PATH = ROOT / "data" / "seen.json"


def load_picks() -> list[dict]:
    if not PICKS_PATH.exists():
        raise FileNotFoundError(f"{PICKS_PATH} not found — run score_candidates.py first.")
    with open(PICKS_PATH, "r") as f:
        picks = json.load(f)
    if not picks:
        raise SystemExit("data/picks.json is empty — nothing to make an issue from.")
    return picks


def load_index() -> list[dict]:
    if not INDEX_PATH.exists():
        return []
    with open(INDEX_PATH, "r") as f:
        return json.load(f)


def load_seen() -> set:
    if not SEEN_PATH.exists():
        return set()
    with open(SEEN_PATH, "r") as f:
        return set(json.load(f))


def save_seen(seen: set) -> None:
    with open(SEEN_PATH, "w") as f:
        json.dump(sorted(seen), f, indent=2)


def main():
    picks = load_picks()
    index = load_index()
    seen = load_seen()

    next_number = (index[-1]["number"] + 1) if index else 1
    issue_id = f"issue-{next_number:03d}"
    today = date.today().isoformat()

    issue = {
        "number": next_number,
        "date": today,
        "picks": [
            {
                "title": p["title"],
                "link": p["link"],
                "source": p["source"],
                "blurb": p["blurb"],
                "tag": p["tag"],
            }
            for p in picks
        ],
    }

    ISSUES_DIR.mkdir(parents=True, exist_ok=True)
    issue_path = ISSUES_DIR / f"{issue_id}.json"
    with open(issue_path, "w") as f:
        json.dump(issue, f, indent=2)

    index.append({"number": next_number, "date": today, "id": issue_id})
    with open(INDEX_PATH, "w") as f:
        json.dump(index, f, indent=2)

    for p in picks:
        seen.add(p["link"])
    save_seen(seen)

    print(f"Wrote {issue_path}")
    print(f"Updated {INDEX_PATH} ({len(index)} issue(s) total)")
    print(f"Marked {len(picks)} link(s) as seen")


if __name__ == "__main__":
    main()
