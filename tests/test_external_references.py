"""Tests that institutional references students/instructors must act on
(GitHub repo, Moodle, digital.kenyon.edu/dh, SASS email) are live links,
not unclickable plain text."""
from pathlib import Path

from bs4 import BeautifulSoup

SITE_ROOT = Path(__file__).parent.parent

# Substrings that, wherever they appear in visible page text, must be
# inside an <a> element (a clickable link) rather than bare text.
REFERENCE_SUBSTRINGS = [
    "digital.kenyon.edu",
    "Moodle",
    "sass@kenyon.edu",
    "github.com/jon-chun",
]


def _rel(path):
    return str(path.relative_to(SITE_ROOT))


def _core_pages():
    return sorted((SITE_ROOT / "core").glob("*.html"))


def test_institutional_references_are_linked():
    failures = []
    for path in _core_pages():
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
        content = soup.select_one(".page-content")
        for string in content.find_all(string=True):
            for needle in REFERENCE_SUBSTRINGS:
                if needle in string:
                    if string.find_parent("a") is None:
                        failures.append(f"{_rel(path)}: '{needle}' not inside <a> (text: '{string.strip()[:80]}')")
    assert not failures, f"Unlinked institutional references: {failures}"
