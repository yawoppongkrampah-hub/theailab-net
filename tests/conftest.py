import pytest
from pathlib import Path
from bs4 import BeautifulSoup

SITE_ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def site_root():
    return SITE_ROOT


@pytest.fixture(scope="session")
def all_html_files(site_root):
    """All HTML files in the site, excluding .venv."""
    return sorted(
        f for f in site_root.rglob("*.html")
        if ".venv" not in f.relative_to(site_root).parts
    )


@pytest.fixture(scope="session")
def parsed_pages(all_html_files):
    """Pre-parsed (path, html_string, soup) tuples for every HTML page."""
    pages = []
    for f in all_html_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(text, "lxml")
        pages.append((f, text, soup))
    return pages


@pytest.fixture(scope="session")
def nav_pages(all_html_files):
    """All HTML files except 404.html.

    404.html is designed to be served by a host that rewrites unmatched
    requests to it (e.g., a static-host redirect rule). No such rule is
    currently configured — the site runs via `python3 -m http.server`,
    which has no custom-404 mechanism — so 404.html is unreachable in
    practice today. It's kept as forward-compatible scaffolding and
    excluded from nav-consistency and reachability checks.
    """
    return [f for f in all_html_files if f.name != "404.html"]
