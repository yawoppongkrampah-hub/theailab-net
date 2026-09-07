"""Integration tests: internal links resolve, nav is consistent, schedule links all weeks."""
import pytest
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import unquote

SITE_ROOT = Path(__file__).parent.parent

EXPECTED_NAV_LABELS = {"Home", "Syllabus", "Schedule", "Assignments", "Policies", "About"}


def _rel(path):
    return str(path.relative_to(SITE_ROOT))


def _resolve_href(href, page_path):
    """Resolve a relative href to an absolute Path, or None for external/anchor/mailto links."""
    if not href or href.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
        return None
    href = href.split("#")[0]
    if not href:
        return None
    href = unquote(href)
    if href.startswith("/"):
        return (SITE_ROOT / href.lstrip("/")).resolve()
    return (page_path.parent / href).resolve()


def _collect_broken_links(page_path, soup, selector="a"):
    broken = []
    for tag in soup.select(selector):
        href = tag.get("href", "")
        target = _resolve_href(href, page_path)
        if target is not None and not target.exists():
            broken.append(href)
    return broken


class TestAllInternalLinks:
    def test_all_internal_links_resolve(self, site_root, parsed_pages):
        """Every internal <a href> across all pages must resolve to an existing file."""
        broken = []
        for path, _, soup in parsed_pages:
            for bad in _collect_broken_links(path, soup):
                broken.append(f"{_rel(path)} -> {bad}")
        assert not broken, f"{len(broken)} broken internal links. First 15: {broken[:15]}"


class TestNavConsistency:
    def test_all_nav_pages_have_identical_nav_labels(self, site_root, nav_pages):
        """Every page (except 404.html) must have the exact same set of nav link labels."""
        failures = []
        for f in nav_pages:
            soup = BeautifulSoup(f.read_text(encoding="utf-8"), "lxml")
            nav = soup.select_one("nav.main-nav")
            if not nav:
                failures.append(f"{_rel(f)}: missing nav.main-nav")
                continue
            labels = {a.get_text(strip=True) for a in nav.find_all("a")}
            if labels != EXPECTED_NAV_LABELS:
                failures.append(f"{_rel(f)}: {sorted(labels)}")
        assert not failures, f"Pages with inconsistent nav labels: {failures[:15]}"

    def test_nav_links_resolve(self, site_root, nav_pages):
        """Nav links on every non-404 page must resolve to existing files."""
        broken = []
        for f in nav_pages:
            soup = BeautifulSoup(f.read_text(encoding="utf-8"), "lxml")
            nav = soup.select_one("nav.main-nav")
            if not nav:
                continue
            for link in _collect_broken_links(f, nav, "a"):
                broken.append(f"{_rel(f)} -> {link}")
        assert not broken, f"Broken nav links: {broken[:15]}"


class TestCoreNavLinkStyle:
    def test_core_pages_use_bare_relative_links_to_sibling_core_pages(self, site_root):
        """core/*.html pages must link to sibling core/ pages with the bare
        '<page>.html' form, not the redundant '../core/<page>.html' form."""
        core_dir = site_root / "core"
        failures = []
        for f in sorted(core_dir.glob("*.html")):
            soup = BeautifulSoup(f.read_text(encoding="utf-8"), "lxml")
            nav = soup.select_one("nav.main-nav")
            for a in nav.find_all("a"):
                href = a.get("href", "")
                if href.startswith("../core/"):
                    failures.append(f"{_rel(f)} -> {href}")
        assert not failures, f"core/ pages using verbose '../core/' nav links: {failures}"

    def test_active_nav_link_attribute_order_is_consistent(self, site_root):
        """The active-nav-link marker should consistently be written as
        <a href="..." class="active">, not <a class="active" href="...">."""
        core_dir = site_root / "core"
        failures = []
        for f in sorted(core_dir.glob("*.html")):
            text = f.read_text(encoding="utf-8")
            if '<a class="active" href=' in text:
                failures.append(_rel(f))
        assert not failures, f"core/ pages with class-before-href attribute order: {failures}"


class TestScheduleLinksAllWeeks:
    def test_schedule_links_to_all_15_weeks(self, site_root):
        """core/schedule.html must link to weeks/week-01.html through weeks/week-15.html."""
        schedule = site_root / "core" / "schedule.html"
        soup = BeautifulSoup(schedule.read_text(encoding="utf-8"), "lxml")
        hrefs = {a.get("href", "") for a in soup.find_all("a")}
        missing = []
        for n in range(1, 16):
            expected = f"../weeks/week-{n:02d}.html"
            alt = f"weeks/week-{n:02d}.html"
            if expected not in hrefs and alt not in hrefs and not any(
                h.endswith(f"week-{n:02d}.html") for h in hrefs
            ):
                missing.append(f"week-{n:02d}.html")
        assert not missing, f"core/schedule.html missing links to: {missing}"

    def test_schedule_link_text_matches_week_title(self, site_root):
        """Each week link's text on the Schedule page must match that week
        page's own <h1>, so the two can't silently drift apart."""
        schedule = site_root / "core" / "schedule.html"
        soup = BeautifulSoup(schedule.read_text(encoding="utf-8"), "lxml")
        mismatches = []
        for n in range(1, 16):
            week_file = f"week-{n:02d}.html"
            link = soup.find("a", href=lambda h: h and h.endswith(week_file))
            assert link is not None, f"No schedule link found for {week_file}"
            week_path = site_root / "weeks" / week_file
            week_soup = BeautifulSoup(week_path.read_text(encoding="utf-8"), "lxml")
            actual_title = week_soup.find("h1").get_text(strip=True)
            link_text = link.get_text(strip=True)
            if link_text != actual_title:
                mismatches.append(f"{week_file}: schedule says '{link_text}', page h1 is '{actual_title}'")
        assert not mismatches, f"Schedule link text drifted from week page title: {mismatches}"
