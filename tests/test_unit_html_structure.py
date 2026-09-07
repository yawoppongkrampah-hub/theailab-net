"""Unit tests: every HTML page has valid structure and required elements."""
from pathlib import Path

SITE_ROOT = Path(__file__).parent.parent

TITLE_SUFFIX = "– IPHS 400: Frontiers in AI"  # en dash
FOOTER_TEXT = "IPHS 400: Frontiers in AI · Kenyon College"


def _rel(path):
    return str(path.relative_to(SITE_ROOT))


class TestDoctype:
    def test_all_pages_have_doctype(self, parsed_pages):
        """Every HTML page must begin with <!DOCTYPE html>."""
        failures = []
        for path, text, _ in parsed_pages:
            if not text.strip().lower().startswith("<!doctype html"):
                failures.append(_rel(path))
        assert not failures, f"Pages missing <!DOCTYPE html>: {failures[:15]}"


class TestTitle:
    def test_all_titles_end_with_course_suffix(self, parsed_pages):
        """Every <title> must end with '{TITLE_SUFFIX}'."""
        failures = []
        for path, _, soup in parsed_pages:
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            if not title.endswith(TITLE_SUFFIX):
                failures.append(f"{_rel(path)}: '{title}'")
        assert not failures, f"Titles not ending with course suffix: {failures[:15]}"


class TestCSSLink:
    def test_all_pages_link_to_resolvable_style_css(self, parsed_pages):
        """Every page must have a <link rel='stylesheet'> to a resolvable css/style.css."""
        failures = []
        for path, _, soup in parsed_pages:
            links = [
                tag for tag in soup.find_all("link", rel="stylesheet")
                if "style.css" in tag.get("href", "")
            ]
            if not links:
                failures.append(f"{_rel(path)}: no stylesheet link")
                continue
            href = links[0]["href"]
            target = (path.parent / href).resolve()
            if not target.exists():
                failures.append(f"{_rel(path)}: href '{href}' does not resolve")
        assert not failures, f"CSS link issues: {failures[:15]}"


class TestHeaderFooterHero:
    def test_all_pages_have_site_header(self, parsed_pages):
        """Every page must contain a <header class="site-header">."""
        failures = [_rel(p) for p, _, s in parsed_pages if not s.select_one("header.site-header")]
        assert not failures, f"Pages missing header.site-header: {failures[:15]}"

    def test_all_pages_have_site_footer_with_text(self, parsed_pages):
        """Every page must contain a <footer class="site-footer"> with the course footer text."""
        failures = []
        for path, _, soup in parsed_pages:
            footer = soup.select_one("footer.site-footer")
            if not footer:
                failures.append(f"{_rel(path)}: missing footer.site-footer")
                continue
            if FOOTER_TEXT not in footer.get_text():
                failures.append(f"{_rel(path)}: footer text mismatch")
        assert not failures, f"Footer issues: {failures[:15]}"

    def test_all_pages_have_hero_with_h1(self, parsed_pages):
        """Every page must have a <section class="hero"> containing an <h1>."""
        failures = []
        for path, _, soup in parsed_pages:
            hero = soup.select_one("section.hero")
            if not hero:
                failures.append(f"{_rel(path)}: missing section.hero")
                continue
            if not hero.find("h1"):
                failures.append(f"{_rel(path)}: hero has no h1")
        assert not failures, f"Hero section issues: {failures[:15]}"


class TestNoLeftoverBranding:
    def test_no_programming_humanity_text(self, parsed_pages):
        """No page should contain leftover 'Programming Humanity' template branding."""
        failures = [
            _rel(path) for path, text, _ in parsed_pages
            if "Programming Humanity" in text
        ]
        assert not failures, f"Pages with leftover 'Programming Humanity' text: {failures[:15]}"

    def test_no_placeholder_notice(self, parsed_pages):
        """No page should contain a .placeholder-notice element."""
        failures = [
            _rel(path) for path, _, soup in parsed_pages
            if soup.select_one(".placeholder-notice")
        ]
        assert not failures, f"Pages with .placeholder-notice: {failures[:15]}"

    def test_no_stub_or_placeholder_strings(self, parsed_pages):
        """No page should contain literal 'Lorem ipsum', 'TBD', or 'TODO' text."""
        failures = []
        for path, text, _ in parsed_pages:
            hits = [s for s in ("Lorem ipsum", "TBD", "TODO") if s in text]
            if hits:
                failures.append(f"{_rel(path)}: {hits}")
        assert not failures, f"Pages with stub/placeholder strings: {failures[:15]}"


class TestActiveNavAria:
    def test_active_nav_link_has_aria_current(self, parsed_pages):
        """Every non-404 page's active nav link must carry aria-current="page"
        so assistive tech gets the same "you are here" signal sighted users
        get from the .active CSS class."""
        failures = []
        for path, _, soup in parsed_pages:
            if path.name == "404.html":
                continue
            active = soup.select_one("nav.main-nav a.active")
            if active is None or active.get("aria-current") != "page":
                failures.append(_rel(path))
        assert not failures, f"Pages missing aria-current on active nav link: {failures[:15]}"


class TestNotFoundPageLinks:
    def test_404_links_are_root_relative(self, site_root):
        """404.html has no working local hosting mechanism to serve it
        (python3 -m http.server has no custom-404 rewrite), so if it's ever
        served again via a host-level catch-all rewrite from a non-root URL,
        its own links must resolve correctly regardless of the request path
        that triggered it — which requires root-relative hrefs."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup((site_root / "404.html").read_text(encoding="utf-8"), "lxml")
        bad = [
            a["href"] for a in soup.find_all("a", href=True)
            if not a["href"].startswith(("/", "#"))
        ]
        assert not bad, f"404.html links must be root-relative (same-page '#' anchors are fine): {bad}"


class TestSkipLink:
    def test_all_pages_have_skip_link_to_main(self, parsed_pages):
        """Every page must have a skip-to-content link as the first focusable
        element, jumping to a #main-content anchor on <main>."""
        failures = []
        for path, _, soup in parsed_pages:
            skip = soup.select_one("a.skip-link[href='#main-content']")
            main = soup.select_one("main#main-content")
            if not skip or not main:
                failures.append(_rel(path))
        assert not failures, f"Pages missing skip-link/#main-content pair: {failures[:15]}"


class TestTableAccessibility:
    def test_all_th_have_scope(self, parsed_pages):
        """Every <th> must declare scope="col" or scope="row" for screen readers."""
        failures = []
        for path, _, soup in parsed_pages:
            for th in soup.find_all("th"):
                if not th.get("scope"):
                    failures.append(_rel(path))
                    break
        assert not failures, f"Pages with <th> missing scope attribute: {failures[:15]}"

    def test_all_tables_have_caption(self, parsed_pages):
        """Every <table> must have a <caption> describing its content."""
        failures = []
        for path, _, soup in parsed_pages:
            for table in soup.find_all("table"):
                if not table.find("caption"):
                    failures.append(_rel(path))
                    break
        assert not failures, f"Pages with <table> missing <caption>: {failures[:15]}"


class TestContentNotEmpty:
    def test_page_content_has_minimum_text(self, parsed_pages):
        """Every page's .page-content div must have at least 20 characters of stripped text."""
        failures = []
        for path, _, soup in parsed_pages:
            content_div = soup.select_one(".page-content")
            if not content_div:
                failures.append(f"{_rel(path)}: missing .page-content")
                continue
            text = content_div.get_text(strip=True)
            if len(text) < 20:
                failures.append(f"{_rel(path)}: only {len(text)} chars")
        assert not failures, f"Pages with near-empty .page-content: {failures[:15]}"
