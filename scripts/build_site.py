"""
Step 5 — Static site builder.

Reads data/issues/index.json and every data/issues/issue-*.json, renders
them through the templates in templates/, and writes the result to
docs/ (index.html + issues/issue-XXX.html). docs/ is what gets served by
GitHub Pages — see step 7.

Usage:
    python scripts/build_site.py
"""

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
ISSUES_DIR = ROOT / "data" / "issues"
INDEX_PATH = ISSUES_DIR / "index.json"
TEMPLATES_DIR = ROOT / "templates"
DOCS_DIR = ROOT / "docs"

SITE_TITLE = "the reading corner"
SITE_TAGLINE = "a weekly handful of things worth reading"


def load_index() -> list[dict]:
    if not INDEX_PATH.exists():
        return []
    with open(INDEX_PATH, "r") as f:
        return json.load(f)


def load_issue(issue_id: str) -> dict:
    with open(ISSUES_DIR / f"{issue_id}.json", "r") as f:
        return json.load(f)


def main():
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    index = load_index()
    # newest issue first on the homepage
    index_newest_first = sorted(index, key=lambda i: i["number"], reverse=True)

    (DOCS_DIR / "issues").mkdir(parents=True, exist_ok=True)

    index_template = env.get_template("index.html.j2")
    homepage_html = index_template.render(
        site_title=SITE_TITLE,
        site_tagline=SITE_TAGLINE,
        issues=index_newest_first,
    )
    (DOCS_DIR / "index.html").write_text(homepage_html)
    print(f"Wrote {DOCS_DIR / 'index.html'}")

    issue_template = env.get_template("issue.html.j2")
    for entry in index:
        issue = load_issue(entry["id"])
        issue_html = issue_template.render(site_title=SITE_TITLE, issue=issue)
        out_path = DOCS_DIR / "issues" / f"{entry['id']}.html"
        out_path.write_text(issue_html)
        print(f"Wrote {out_path}")

    print(f"\nSite built for {len(index)} issue(s). Open docs/index.html to preview.")


if __name__ == "__main__":
    main()
