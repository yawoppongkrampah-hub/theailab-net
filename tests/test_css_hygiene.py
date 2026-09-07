"""Tests that css/style.css doesn't carry selectors unreachable from any HTML page."""
import re
from pathlib import Path

SITE_ROOT = Path(__file__).parent.parent

# Class-selector names that must not appear in css/style.css at all: dead
# blog-theme cruft inherited from the WordPress "Twenty Nineteen" theme this
# site was adapted from, confirmed unreferenced by any current HTML page.
DEAD_CLASSES = [
    "has-featured-image", "featured-media", "social-nav", "entry-meta",
    "entry-footer", "post-nav", "share-links", "post-preview",
    "other-blog-pages", "columns", "wp-block-image", "wp-block-separator",
    "badge", "badge-draft", "badge-private", "badge-placeholder",
    "placeholder-notice", "page-meta",
]


def test_style_css_has_no_dead_selectors():
    css = (SITE_ROOT / "css" / "style.css").read_text(encoding="utf-8")
    found = [c for c in DEAD_CLASSES if re.search(rf"\.{re.escape(c)}\b", css)]
    assert not found, f"css/style.css still defines dead selectors: {found}"
