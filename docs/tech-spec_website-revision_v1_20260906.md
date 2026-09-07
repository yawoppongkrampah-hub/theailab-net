# Tech Spec: Website Revisions — theailab-net (IPHS 400)

**Date:** 2026-09-06
**Source:** Synthesized from `docs/report_web-revision_v1_20260906.md` (and, by inheritance, `docs/report_web-revison_v1_20260901.md`)
**Scope:** All revisions below apply to the site as it exists today — a standalone static site (22 HTML pages, one stylesheet, a pytest suite) with no build step, no deploy pipeline, and no external hosting config. It is run and tested via `python3 -m http.server`.
**Format:** Each task is a self-contained unit of work: description, justification, and step-by-step implementation instructions concrete enough to execute without re-reading the source critique. Tasks are grouped by criticality (`high` / `medium` / `low`) and numbered `T1`–`T10` for cross-reference.

---

## How to use this document

Work top-to-bottom within a criticality band; bands themselves are ordered `high` → `medium` → `low`. Several tasks touch the same files — where that happens, it's called out in "Depends on / conflicts with" so they can be batched into one edit pass instead of round-tripping the same file three times. After each task, the "Verify" step says exactly how to confirm it worked; run the full suite (`pytest tests/ -v`) after each completed task regardless, since several tasks add new tests that all subsequent work must keep passing.

---

## HIGH criticality

### T1 — Fix the 5 mismatched week titles on `core/schedule.html`

**Description:** `core/schedule.html` links to each week page using its own copy of that week's title as link text. For Weeks 6, 10, 13, 14, and 15, that copy has drifted from the destination page's actual title.

**Justification:** This is the only outright content bug in the site — a visitor reading the Schedule page is told a different (longer) title than the one the actual week page uses in its `<title>`, `<h1>`, and breadcrumb. Those three elements agree with each other on every affected week page, which makes the *shorter* title the clearly authoritative one and `schedule.html`'s copy the outlier. It's a trivial fix with outsized correctness payoff, and it's been sitting open since the 2026-09-01 report with no regression test to prevent recurrence.

**Steps:**
1. Open `core/schedule.html`.
2. Make these five exact text replacements inside the `<a href="../weeks/week-NN.html">...</a>` link text (leave the `href` targets untouched — they already point to the right files):

   | Week | Find | Replace with |
   |---|---|---|
   | 6 | `Week 6: Hooks Architecture and Guardrails` | `Week 6: Hooks Architecture` |
   | 10 | `Week 10: MP3 Demos and the Spec-Driven Development Landscape` | `Week 10: MP3 Demos and the Spec-Driven Landscape` |
   | 13 | `Week 13: Full-Cycle Capstone Work Session and MP4 Presentations` | `Week 13: Full-Cycle Capstone Work Session` |
   | 14 | `Week 14: Final Project Work Session and Poster Development` | `Week 14: Final Project Work Session` |
   | 15 | `Week 15: Final Project Poster Presentations` | `Week 15: Final Project Presentations` |

3. Save the file. Do not touch any other line — the other 10 week links already match.
4. Add the regression test from **T3, Part A** in the same work session so this can't silently drift again (that test doubles as verification for this fix).

**Verify:** Re-run `grep -oE '<a href="\.\./weeks/week-[0-9]+\.html">[^<]*</a>' core/schedule.html` and confirm all 15 link-text strings now exactly match the corresponding `weeks/week-NN.html`'s `<h1>` text. Then run `pytest tests/ -v` — all existing tests should still pass, plus the new test from T3 if added.

---

### T2 — Resolve `404.html`'s broken hosting assumption

**Description:** `404.html` was built to be served via a Netlify redirect rule (`[[redirects]] from = "/*" to = "/404.html" status = 404`) that was removed earlier this session along with all other Netlify/CI config. Under `python3 -m http.server` — the site's only supported run mode now — there is no mechanism that serves this file for a bad URL; Python's built-in server returns its own plain-text 404 instead. Separately, the page's own internal links (`href="index.html"`, `href="core/syllabus.html"`) are written relative to the file's own location, which breaks if it's ever served again via a root-level catch-all rewrite from a non-root URL (e.g., a request for `/weeks/typo.html` would resolve `index.html` to `/weeks/index.html`).

**Justification:** Right now the repo carries a page, a CSS block, and test coverage for a feature (a custom "page not found" experience) that cannot actually be triggered in the site's current run mode. That's a real gap between what the test suite implies works and what a person running the site locally will ever see — worth closing explicitly rather than leaving it to be discovered later. The recommended fix (Option B below) is the less destructive path: it keeps the page for whenever hosting is reintroduced, fixes the latent link bug so it's actually correct next time, and documents the current limitation instead of silently hiding it.

**Steps (Option B — recommended: keep the page, fix its links, document the limitation):**
1. Open `404.html`. Change the two body links from page-relative to root-relative:
   - `<a href="index.html">IPHS 400: Frontiers in AI</a>` → `<a href="/index.html">IPHS 400: Frontiers in AI</a>`
   - Each `<li><a href="core/syllabus.html">Syllabus</a></li>`-style nav link and the `<a href="index.html">← Home</a>` link in the body → prefix each `href` with `/` (e.g., `/core/syllabus.html`, `/index.html`).
2. Open `README.md`. In the "Repository Structure" tree, add a one-line comment next to the `404.html` entry noting the limitation, e.g.:
   ```
   ├── 404.html                 # Not-found page (not auto-served by `python3 -m http.server`; kept for future hosting)
   ```
3. Open `tests/conftest.py`. The `nav_pages` fixture's docstring already explains the *exclusion* reasoning ("404.html is a server-served fallback page..."); update it to also note that no current run mode actually serves it:
   ```python
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
   ```
4. (Optional, if root-relative link resolution should be verified automatically) Add a small unit test asserting every `href` inside `404.html`'s `<body>` starts with `/`:
   ```python
   class TestNotFoundPageLinks:
       def test_404_links_are_root_relative(self, site_root):
           from bs4 import BeautifulSoup
           soup = BeautifulSoup((site_root / "404.html").read_text(encoding="utf-8"), "lxml")
           bad = [a["href"] for a in soup.find_all("a", href=True) if not a["href"].startswith("/")]
           assert not bad, f"404.html links must be root-relative: {bad}"
   ```
   Place this in `tests/test_unit_html_structure.py`.

**Steps (Option A — alternative: delete it entirely):** Only choose this if the decision is made that a not-found page has no place in a purely local, no-hosting site. If so: `rm 404.html`; remove `"404.html"` from the `@pytest.mark.parametrize` list in `tests/test_e2e_site.py`'s `test_required_root_files_exist`; change `EXPECTED_TOTAL_PAGES = 22` to `21` in the same file; remove the now-dead `nav_pages` fixture from `tests/conftest.py` and replace its two call sites in `tests/test_integration_links.py` with the plain `all_html_files` fixture; remove the `404.html` line from the README's Repository Structure tree.

**Verify:** Run `pytest tests/ -v` — full suite green under whichever option was chosen. For Option B, additionally open `404.html` directly in a browser (`file://` or via `python3 -m http.server`) and click every link to confirm they still resolve correctly when the page is loaded from the site root.

---

### T3 — Add regression tests for the three duplicated content blocks

**Description:** Three blocks of policy-relevant text exist verbatim in two files each, with no mechanism to catch drift when one copy is edited and the other is forgotten:
- **Part A** — `<h2>Course Description</h2>` through the "Outcome 6 is assessed..." paragraph, duplicated between `core/about.html` and `core/syllabus.html`.
- **Part B** — the "Summary of Assignments and Weights" table, duplicated between `core/syllabus.html` and `core/assignments.html`.
- **Part C** — the four-bullet "Secrets Hygiene and Agent Safety" list, duplicated between `core/syllabus.html` and `core/policies.html` (the *list content* is identical; the wrapping heading differs in level and wording between the two files, so the test must compare the `<ul>` body only, not the heading).

**Justification:** With no build step or include mechanism, these three blocks are three separate places a future edit has to remember to touch — and the syllabus itself warns that tooling/dates will be revised mid-semester, so an edit is not a hypothetical. A test that fails loudly the moment the two copies diverge is far cheaper than a policy inconsistency (e.g., different secrets-hygiene rules in two places) discovered by a student or the instructor after the fact.

**Steps:**
1. Create a new test file `tests/test_content_sync.py`.
2. Implement a helper that extracts the substring between two markers found *in that order* within a file's raw text (not the DOM), since the goal is exact-text comparison, not structural comparison:
   ```python
   """Tests that verify duplicated content blocks stay byte-for-byte in sync."""
   import re
   from pathlib import Path

   SITE_ROOT = Path(__file__).parent.parent


   def _extract(path, start_marker, end_marker):
       text = path.read_text(encoding="utf-8")
       start = text.index(start_marker)
       end = text.index(end_marker, start) + len(end_marker)
       return text[start:end]


   def _normalize(s):
       return re.sub(r"\s+", " ", s).strip()
   ```
3. Add Part A (about.html ↔ syllabus.html):
   ```python
   def test_course_description_block_matches_about_and_syllabus():
       about = SITE_ROOT / "core" / "about.html"
       syllabus = SITE_ROOT / "core" / "syllabus.html"
       start = "<h2>Course Description</h2>"
       end = ("Outcome 6 is assessed through the ethics discussions in Weeks 3, 8, "
              "and 12, related quiz questions, and the lightning presentation. "
              "Outcomes 1–5 map to Mini-Projects 1–4; Outcomes 7–9 "
              "map to the Final Project.</p>")
       block_about = _normalize(_extract(about, start, end))
       block_syllabus = _normalize(_extract(syllabus, start, end))
       assert block_about == block_syllabus, (
           "core/about.html and core/syllabus.html have drifted in their shared "
           "Course Description / Learning Outcomes block. Update both to match, "
           "or intentionally diverge and delete this test."
       )
   ```
   Note the `–` escapes for the en dash (`–`) in the marker text — copy this exactly rather than retyping the dash character, to avoid an encoding mismatch.
4. Add Part B (syllabus.html ↔ assignments.html):
   ```python
   def test_assignment_weights_table_matches_syllabus_and_assignments():
       syllabus = SITE_ROOT / "core" / "syllabus.html"
       assignments = SITE_ROOT / "core" / "assignments.html"
       start = "<h2>Summary of Assignments and Weights</h2>"
       end = "<tr><th>Total</th><th>100%</th><td></td></tr>\n</table>"
       block_syllabus = _normalize(_extract(syllabus, start, end))
       block_assignments = _normalize(_extract(assignments, start, end))
       assert block_syllabus == block_assignments, (
           "core/syllabus.html and core/assignments.html have drifted in the "
           "assignment-weights table. Update both to match."
       )
   ```
5. Add Part C (syllabus.html ↔ policies.html) — compare only the `<ul>...</ul>` body, since the wrapping heading intentionally differs (`<h3>Secrets Hygiene and Agent Safety (required practice for all projects)</h3>` in syllabus.html vs. `<h2>Secrets Hygiene and Agent Safety</h2>` in policies.html):
   ```python
   def test_secrets_hygiene_list_matches_syllabus_and_policies():
       syllabus = SITE_ROOT / "core" / "syllabus.html"
       policies = SITE_ROOT / "core" / "policies.html"
       start = "<li><strong>Never commit API keys"
       end = "There is no penalty for prompt disclosure.</li>\n</ul>"
       block_syllabus = _normalize(_extract(syllabus, start, end))
       block_policies = _normalize(_extract(policies, start, end))
       assert block_syllabus == block_policies, (
           "core/syllabus.html and core/policies.html have drifted in the "
           "Secrets Hygiene and Agent Safety bullet list. Update both to match. "
           "(Only the <ul> body is compared — the wrapping heading is allowed "
           "to differ between the two contexts.)"
       )
   ```
6. Run `pytest tests/test_content_sync.py -v` in isolation first to confirm all three pass against the current (still-duplicated, still-in-sync) content, before running the full suite.

**Depends on / conflicts with:** None of the other tasks edit the text inside these three blocks, so this can be done independently and first.

**Verify:** `pytest tests/test_content_sync.py -v` — 3 passed. Then, as a sanity check that the tests actually catch drift, temporarily change one word in one copy of any block, re-run, confirm it fails, then revert the change before committing.

---

## MEDIUM criticality

### T4 — Add `aria-current="page"` to active nav links and `:focus-visible` styling

**Description:** The current page in the top nav is indicated only by `class="active"` (a CSS-only signal). There is no `aria-current="page"` attribute for assistive technology, and `style.css` defines `:hover` treatments for links and nav items but no `:focus`/`:focus-visible` rule anywhere.

**Justification:** These are the two accessibility gaps most likely to be noticed by an actual keyboard or screen-reader user testing the site locally (an instructor, a TA, or a student with a disability), independent of whether the site is ever hosted publicly. Both are small, mechanical fixes.

**Steps — `aria-current`:**
1. Every page has exactly one nav link with `class="active"` (21 pages: `index.html`, all 5 `core/*.html`, all 15 `weeks/*.html` — `404.html` has no active link and should stay that way). On each, add `aria-current="page"` alongside the existing class. For example, in `index.html`:
   - Before: `<li><a href="index.html" class="active">Home</a></li>`
   - After: `<li><a href="index.html" class="active" aria-current="page">Home</a></li>`
2. Because this is a mechanical, identical edit repeated 21 times, do it with a scripted find-and-replace rather than 21 manual edits. From the repo root:
   ```bash
   grep -rl 'class="active"' index.html core weeks | while read -r f; do
     sed -i '' 's/class="active"/class="active" aria-current="page"/' "$f"
   done
   ```
   (The `-i ''` flag is for macOS/BSD `sed`; on GNU/Linux `sed`, use `-i` with no argument.)
3. Spot-check 2–3 files afterward (e.g., `index.html`, `core/schedule.html`, `weeks/week-08.html`) to confirm exactly one `aria-current="page"` was added per file, on the correct link.

**Steps — `:focus-visible`:**
4. Open `css/style.css`. Add a focus-visible rule near the existing hover rules for nav and in-content links (after the `.main-nav li a:hover, .main-nav li a.active` block around line 176–183):
   ```css
   .main-nav li a:focus-visible {
     text-decoration: underline;
     text-decoration-thickness: 2px;
     text-underline-offset: 4px;
     outline: 2px solid var(--accent);
     outline-offset: 2px;
   }
   ```
5. Add a general focus-visible rule for in-content and footer links, near the base `a`/`a:hover` rules (after line 44):
   ```css
   a:focus-visible {
     outline: 2px solid var(--accent);
     outline-offset: 2px;
   }
   ```

**Depends on / conflicts with:** None. Independent of all other tasks.

**Verify:** Add a targeted test to `tests/test_unit_html_structure.py`:
```python
class TestActiveNavAria:
    def test_active_nav_link_has_aria_current(self, parsed_pages):
        failures = []
        for path, _, soup in parsed_pages:
            if path.name == "404.html":
                continue
            active = soup.select_one("nav.main-nav a.active")
            if active is None or active.get("aria-current") != "page":
                failures.append(_rel(path))
        assert not failures, f"Pages missing aria-current on active nav link: {failures[:15]}"
```
Run `pytest tests/ -v` — full suite green. Then tab through the nav on `index.html` in a browser and confirm a visible focus ring appears on each link.

---

### T5 — Hyperlink plain-text institutional references

**Description:** Several external resources are referenced as plain text or `<code>` spans instead of clickable links: the course GitHub repo (`core/about.html`, `core/syllabus.html`), `digital.kenyon.edu/dh` (4 mentions across `core/about.html`, `core/syllabus.html`, `core/policies.html`, `core/assignments.html`), "Moodle"/"Moodle.kenyon.edu" (`core/syllabus.html`, `core/about.html`, `core/assignments.html`), and `sass@kenyon.edu` (`core/policies.html`, not even a `mailto:` link).

**Justification:** Every one of these is a resource a student or instructor is expected to actually navigate to (submit work, publish a poster, email accessibility services) — leaving them as unclickable text is a real usability cost, not a cosmetic one, and it's cheap to fix.

**Steps:**
1. `core/about.html`, line ~60 — GitHub repo:
   - Before: `<li>Materials: <code>https://github.com/jon-chun/theailab-net</code></li>`
   - After: `<li>Materials: <a href="https://github.com/jon-chun/theailab-net"><code>https://github.com/jon-chun/theailab-net</code></a></li>`
2. `core/syllabus.html`, line ~39 (Course Site table row) — same GitHub repo:
   - Before: `<tr><th>Course Site</th><td><code>https://github.com/jon-chun/theailab-net</code> (materials) and Moodle (quizzes, grades, submissions)</td></tr>`
   - After: `<tr><th>Course Site</th><td><a href="https://github.com/jon-chun/theailab-net"><code>https://github.com/jon-chun/theailab-net</code></a> (materials) and <a href="https://moodle.kenyon.edu">Moodle</a> (quizzes, grades, submissions)</td></tr>`
3. For every remaining plain-text mention of `digital.kenyon.edu/dh` (there are 4 — one each in `core/about.html`, `core/syllabus.html`, `core/policies.html`, `core/assignments.html`), wrap it in a link to `https://digital.kenyon.edu/dh`. Preserve any surrounding `<strong>` tags exactly as they are; only add the `<a>` wrapper. Example, in `core/policies.html`:
   - Before: `...publication at <strong>digital.kenyon.edu/dh</strong> as part of...`
   - After: `...publication at <strong><a href="https://digital.kenyon.edu/dh">digital.kenyon.edu/dh</a></strong> as part of...`
4. For every remaining plain-text mention of "Moodle" (in `core/syllabus.html` line ~117, ~129, and `core/assignments.html` line ~46, ~88) and "Moodle.kenyon.edu" (`core/assignments.html` line ~88), wrap in `<a href="https://moodle.kenyon.edu">...</a>`, keeping the visible text exactly as-is (don't change "Moodle" to "Moodle.kenyon.edu" or vice versa — just add the link).
5. `core/policies.html`, line ~101 — SASS email:
   - Before: `...by emailing sass@kenyon.edu, then to meet...`
   - After: `...by emailing <a href="mailto:sass@kenyon.edu">sass@kenyon.edu</a>, then to meet...`
6. Since T3's content-sync tests do exact-text comparison on some of these blocks, apply the *same* wrapping to both copies of any block T3 covers. Concretely: the "Moodle" mention inside the assignment-submissions sentence appears in both `core/syllabus.html` (line ~117, inside a block **not** covered by a T3 test) and `core/assignments.html` (line ~46, also not covered by a T3 test) — these two sentences are similar but not part of a T3-tracked exact-duplicate block, so they can be edited independently; just make sure both end up linked for consistency.

**Depends on / conflicts with:** Do this *before* T3 if both are being done in the same pass, or re-run the T3 tests immediately after this task to confirm they still pass — T5 does not touch text inside the three T3-tracked block boundaries (the Course Description/Outcomes block, the assignment-weights table, and the secrets-hygiene bullet list contain no plain-text URLs), so the two tasks shouldn't conflict, but re-verifying costs nothing.

**Verify:** `grep -rn "digital.kenyon.edu\|Moodle\|sass@kenyon.edu\|github.com/jon-chun" core/*.html` and manually confirm every remaining occurrence is now inside an `<a href>`. Run `pytest tests/ -v` (the existing `test_all_internal_links_resolve` test only checks *internal* links, so it won't validate these external URLs, but it will confirm nothing else broke). Optionally, open each modified page in a browser and click each new link to confirm it resolves.

---

### T6 — Reconcile inconsistent internal link style and attribute order in `core/`

**Description:** `core/syllabus.html` and `core/schedule.html` link to sibling pages in `core/` using the fully-qualified `../core/<page>.html` form and write `<a class="active" href="...">` (class before href); `core/about.html`, `core/assignments.html`, and `core/policies.html` use the bare `<page>.html` form and write `<a href="..." class="active">` (href before class). Both forms resolve correctly today, so this is a style/consistency fix, not a bug fix.

**Justification:** All five `core/` pages should read as if generated from one template. The bare relative-path form is simpler and already used by 3 of the 5 pages, so it's the natural convention to standardize on. Fixing this now, before any future automated content generation or templating is introduced, avoids baking the inconsistency into whatever comes next.

**Steps:**
1. In `core/syllabus.html`, in the `<nav class="main-nav">` block, replace every sibling link's `../core/` prefix with nothing (keep the `../index.html` Home link as-is, since that one correctly needs to go up a directory):
   - `<a href="../core/syllabus.html">` → `<a href="syllabus.html">` (and similarly for `schedule.html`, `assignments.html`, `policies.html`, `about.html`)
2. Do the same in `core/schedule.html`.
3. In both files, also normalize attribute order on the active-link marker from `<a class="active" href="...">` to `<a href="..." class="active">`, matching the other three `core/` pages.
4. Leave every other file (`index.html`, `404.html`, all `weeks/*.html`) untouched — their nav links correctly use the `../core/` and `../index.html` forms since they live outside `core/`, and this task is scoped to consistency *within* `core/` only.

**Depends on / conflicts with:** Independent of T1–T5. Do not confuse this with T2's `404.html` link fix (different files, different reason — T2 makes 404.html's links root-relative for a hosting-correctness reason; this task makes core/ nav links same-directory-relative for a style-consistency reason).

**Verify:** Run:
```bash
grep -o 'href="[^"]*syllabus.html"' core/*.html
```
and confirm all 5 files now use the bare `syllabus.html"` form (except none should show `../core/`). Then run `pytest tests/ -v` — `test_nav_links_resolve` and `test_all_nav_pages_have_identical_nav_labels` must still pass, since the fix changes href *form* but not href *targets* or link *labels*.

---

### T7 — Remove or flag dead CSS

**Description:** Roughly a fifth of `css/style.css` (620 lines) — inherited from the WordPress "Twenty Nineteen" blog theme this site was adapted from — matches no element in any of the 22 current HTML pages: `.has-featured-image`, `.featured-media` (+ its `::after` rule), `.social-nav`, `.badge`/`.badge-draft`/`.badge-private`/`.badge-placeholder`, `.placeholder-notice`, `.share-links`, `.post-nav`, `.entry-footer`, `.entry-meta`, `.post-preview`, `.other-blog-pages`, `.columns`, `.wp-block-image`, `.wp-block-separator`, and `.page-meta`.

**Justification:** Dead CSS costs nothing at runtime, but it's a maintenance liability: a future editor reading the stylesheet has no signal for which rules are load-bearing versus inherited cruft, and it invites accidental "fixes" to code that renders nothing.

**Steps:**
1. Before deleting anything, re-confirm the list is still accurate (styles could theoretically have been wired up since the last audit):
   ```bash
   for cls in has-featured-image featured-media social-nav entry-meta entry-footer post-nav share-links post-preview other-blog-pages columns wp-block-image wp-block-separator badge badge-draft badge-private badge-placeholder placeholder-notice page-meta; do
     n=$(grep -rl "\"$cls\"\|class=\"[^\"]*\b$cls\b" --include="*.html" . 2>/dev/null | wc -l | tr -d ' ')
     echo "$cls: $n"
   done
   ```
   Every class should report `0`. If any report nonzero, remove it from the deletion list below and investigate why it's now in use.
2. Open `css/style.css` and delete the following blocks in full (identified by their section comments and selector names):
   - The `.site-header.has-featured-image` rule and its `.featured-media` / `.featured-media img` / `.featured-media::after` rules (lines ~70–99).
   - The `.social-nav` and `.social-nav a` rules (lines ~188–199).
   - The `.entry-meta` block (lines ~274–283).
   - The `.entry-footer`, `.post-nav`, `.share-links` (and its `> span`, `> span::before`, `a`, `a:hover` sub-rules) blocks (lines ~286–334).
   - The `.post-preview` (and its `h2`, `h2 a`, `h2 a:hover`, `.entry-meta`, `p` sub-rules) and `.other-blog-pages` blocks (lines ~432–456).
   - The entire `/* Badges */` section: `.badge`, `.badge-draft`, `.badge-private`, `.badge-placeholder` (lines ~462–485).
   - The `/* Placeholder notice */` section: `.placeholder-notice`, `.placeholder-notice h3` (lines ~488–500).
   - The `.columns` rule (lines ~527–530).
   - The `/* WP Block styles */` section: `.wp-block-image`, `.wp-block-separator` (lines ~536–545).
   - The `.page-meta` rule (lines ~266–271).
3. Also remove now-orphaned references to these selectors inside the `@media (max-width: 768px)` block at the bottom of the file: the `.site-header.has-featured-image` and `.featured-media { display: none; }` overrides (lines ~583–590), and the `.columns { column-count: 1; }` and `.post-nav { flex-direction: column; gap: 0.5rem; }` overrides (lines ~612–619).
4. Leave everything else untouched, including `.breadcrumbs` and `.section`/`.item-list` (both are actively used — confirmed by the audit script reporting nonzero for those classes, so they are *not* on the deletion list above).
5. Re-run the check-loop from step 1 after deleting to confirm the file no longer defines any of the removed selectors (it will report `0` because the selector itself no longer exists to search for in HTML — the real check is that `css/style.css` no longer contains those selector names at all: `grep -c "has-featured-image\|social-nav\|badge-draft\|placeholder-notice\|wp-block" css/style.css` should print `0`).

**Depends on / conflicts with:** Independent of T1–T6, but do it *last* among the medium-priority tasks so it doesn't need to be re-diffed against nav/link edits happening in the same file set (it only touches `css/style.css`, so in practice there's no real conflict — this ordering note is a convenience, not a requirement).

**Verify:** Run `pytest tests/ -v` — the existing `test_no_placeholder_notice` test asserts no page contains a `.placeholder-notice` *element*, which remains true (it always was, even before this cleanup, since the class was dead already); nothing in the suite asserts on the CSS file's contents, so no test should be affected either way. Then visually load `index.html`, `core/syllabus.html`, and one `weeks/week-NN.html` page in a browser and confirm the layout is pixel-identical to before the cleanup (dead rules by definition affect nothing, but a visual spot-check is the cheap way to be sure the wrong lines weren't deleted).

---

## LOW criticality

### T8 — Increase contrast headroom on `--text-lt`

**Description:** The `--text-lt: #767676` token (used for the site tagline, breadcrumbs, page-meta rows, and footer text, mostly at 15–16px) computes to a contrast ratio of ~4.54:1 against the `#fff` background — just barely over the WCAG AA threshold of 4.5:1 for normal text, with almost no margin.

**Justification:** Not a failure today, but it's used in several places at once and sits close enough to the line that a slightly different rendering context (monitor calibration, browser zoom rounding, a future minor color tweak) could tip it under. Widening the margin now is a one-line, zero-risk change.

**Steps:**
1. Open `css/style.css`, line 9: `--text-lt: #767676;`.
2. Change to a darker gray with meaningfully more headroom, e.g. `--text-lt: #5c5c5c;` (contrast ratio against white ≈ 5.9:1).
3. Visually confirm the new color still reads as a clearly "muted/secondary" tone relative to the primary `--text: #111` — it should look subtly lighter, not indistinguishable from body text.

**Depends on / conflicts with:** None.

**Verify:** Load `index.html` and `core/schedule.html` in a browser; confirm the site tagline ("Kenyon College — Fall 2026"), breadcrumbs, and footer text are still legible and visually distinct from primary body text, just with a slightly darker tone. Run `pytest tests/ -v` — unaffected, since no test asserts on specific color values.

---

### T9 — Add a skip-to-content link and table `scope`/`caption` attributes

**Description:** Every page repeats an identical 6-item nav before any page content, with no way for a keyboard/screen-reader user to bypass it. Separately, the `<th>` cells in the Course Details, Assignments, Grading Scale, and Grading Rubric tables have no `scope="col"`/`scope="row"`, and no table has a `<caption>`.

**Justification:** Both are well-established, low-effort accessibility affordances. Lower priority than T4 because they affect a narrower set of interactions (tabbing past a 6-item nav is a minor tax; tables without `scope` are still usually inferrable by screen readers for simple header rows), but worth doing in the same pass as other accessibility work.

**Steps — skip link:**
1. Open `css/style.css` and add a visually-hidden-until-focused utility class, near the top of the file after the reset rule:
   ```css
   .skip-link {
     position: absolute;
     left: -9999px;
     top: 0;
     z-index: 100;
     background: var(--bg);
     color: var(--accent);
     padding: 0.75rem 1.25rem;
     border: 2px solid var(--accent);
     font-family: var(--fb);
     font-weight: 700;
   }
   .skip-link:focus {
     left: 1rem;
     top: 1rem;
   }
   ```
2. On every page (21 pages — all except none, `404.html` included since it also has a `<main>` to skip to), add a skip link as the very first element inside `<body>`, before `<header>`:
   ```html
   <a class="skip-link" href="#main-content">Skip to content</a>
   ```
3. On every page, add `id="main-content"` to the existing `<main class="content-wrapper">` tag, making it `<main class="content-wrapper" id="main-content">`.
4. Since this is a mechanical, identical two-part edit repeated across 22 files, script it rather than hand-editing:
   ```bash
   for f in index.html 404.html core/*.html weeks/*.html; do
     sed -i '' 's#<body>#<body>\n<a class="skip-link" href="#main-content">Skip to content</a>#' "$f"
     sed -i '' 's#<main class="content-wrapper">#<main class="content-wrapper" id="main-content">#' "$f"
   done
   ```
   (Adjust `sed -i ''` to `sed -i` on GNU/Linux. Verify the `#` delimiter in the `sed` expression doesn't collide with the `#main-content` string — if it does, switch the `sed` command's delimiter to e.g. `s@...@...@` instead of `s#...#...#`.)
5. Spot-check 2–3 files to confirm both insertions landed correctly and didn't duplicate or mangle surrounding markup.

**Steps — table `scope`/caption:**
6. For every `<table>` in `core/syllabus.html`, `core/assignments.html`, and `core/schedule.html` (wherever an `<th>` row header exists), add `scope="col"` to column headers and `scope="row"` to any row header. Since all of this site's tables use `<th>` only in the header row (not as row labels down the left edge — check each table to confirm), in practice this means adding `scope="col"` to every `<th>` in each table's first `<tr>`. Example, in `core/syllabus.html`'s Grading Scale table:
   - Before: `<tr><th>Grade</th><th>Percentage</th><th>Description</th></tr>`
   - After: `<tr><th scope="col">Grade</th><th scope="col">Percentage</th><th scope="col">Description</th></tr>`
7. Add a `<caption>` as the first child of each `<table>` element, describing its content, e.g.:
   ```html
   <table>
   <caption>Grading scale by percentage range</caption>
   <tr><th scope="col">Grade</th>...
   ```
   Visually, captions will render above the table using the browser default style; if that's visually undesirable, add a small CSS rule scoping `.page-content table caption` to match the `.page-content figcaption` treatment already defined in `css/style.css` (italic, `--text-lt`, centered).

**Depends on / conflicts with:** Independent of T1–T8. If doing this alongside T7 (dead CSS removal), add the new `.skip-link` and `table caption` CSS *after* removing the dead blocks in T7, in the same file, so there's no need to re-locate line numbers mid-edit.

**Verify:** Add two tests to `tests/test_unit_html_structure.py`:
```python
class TestSkipLink:
    def test_all_pages_have_skip_link_to_main(self, parsed_pages):
        failures = []
        for path, _, soup in parsed_pages:
            skip = soup.select_one("a.skip-link[href='#main-content']")
            main = soup.select_one("main#main-content")
            if not skip or not main:
                failures.append(_rel(path))
        assert not failures, f"Pages missing skip-link/#main-content pair: {failures[:15]}"


class TestTableAccessibility:
    def test_all_th_have_scope(self, parsed_pages):
        failures = []
        for path, _, soup in parsed_pages:
            for th in soup.find_all("th"):
                if not th.get("scope"):
                    failures.append(_rel(path))
                    break
        assert not failures, f"Pages with <th> missing scope attribute: {failures[:15]}"
```
Run `pytest tests/ -v` — full suite green. Then manually tab from the browser address bar into any page and confirm the skip link is the first focusable element and correctly jumps focus to the main content region when activated.

---

### T10 — Deferred: SEO/social meta, favicon, `robots.txt`/`sitemap.xml`, HTTP security headers

**Description:** No page has `<meta name="description">`, Open Graph/Twitter Card tags, or a favicon; there's no `robots.txt` or `sitemap.xml`; and no HTTP security headers are configured (they previously lived in `netlify.toml`, which was removed).

**Justification for deferral, not omission:** Every item in this group is a hosting-layer or search/social-discovery concern. The project's explicit current scope is a standalone site that only ever runs locally via `python3 -m http.server` — there is no public URL for a search engine to crawl, no social-media link preview to generate, and no HTTP response layer to attach security headers to (a local static-file server serves raw files with no header configuration surface). Implementing these now would be effort spent on a problem the site doesn't have yet. This task is recorded here, not deleted, so it can be picked up as a fast-follow the moment hosting is reintroduced.

**Steps (to execute only if/when the site is hosted again):**
1. Add a per-page `<meta name="description" content="...">` tag to each page's `<head>`, with unique, page-specific copy (not a single repeated string) — e.g., for `core/schedule.html`: `<meta name="description" content="Full 15-week schedule for IPHS 400: Frontiers in AI at Kenyon College, Fall 2026.">`.
2. Add a shared `og:title`, `og:description`, `og:type`, and `og:site_name` set to each page (values can mirror the `<title>` and new meta description), plus one `og:image` if a course/site image becomes available.
3. Create a simple favicon (even a plain text/emoji-based one is sufficient for a course site) and reference it via `<link rel="icon" href="/favicon.ico">` (or an SVG favicon) on every page.
4. Add a minimal `robots.txt` at the repo root (`User-agent: *` / `Allow: /`) and a `sitemap.xml` listing all 21 non-404 pages, once a real hosting URL exists (the sitemap needs absolute URLs, which don't exist in a local-only context).
5. Re-introduce HTTP security headers (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Content-Security-Policy`, `Strict-Transport-Security`) via whatever the new hosting layer's config mechanism is (a `netlify.toml`-equivalent, a `vercel.json`, an nginx/Apache config, or GitHub Pages' more limited options) — this is inherently hosting-provider-specific, so exact syntax depends on what's chosen at that time.

**Verify:** Not applicable until a hosting decision is made. When it is, re-open this task and validate each addition against the relevant provider's documentation and a link-preview debugger (e.g., Facebook's Sharing Debugger or Twitter's Card Validator) for the OG/Twitter tags specifically.

---

## Summary Table

| ID | Task | Criticality | Files touched |
|---|---|---|---|
| T1 | Fix 5 mismatched week titles in `core/schedule.html` | High | `core/schedule.html` |
| T2 | Resolve `404.html`'s broken hosting assumption | High | `404.html`, `README.md`, `tests/conftest.py`, (optional) `tests/test_unit_html_structure.py` |
| T3 | Add regression tests for the 3 duplicated content blocks | High | `tests/test_content_sync.py` (new) |
| T4 | `aria-current="page"` + `:focus-visible` styling | Medium | `index.html`, all `core/*.html`, all `weeks/*.html`, `css/style.css`, `tests/test_unit_html_structure.py` |
| T5 | Hyperlink plain-text institutional references | Medium | `core/about.html`, `core/syllabus.html`, `core/policies.html`, `core/assignments.html` |
| T6 | Reconcile link style/attribute order in `core/` | Medium | `core/syllabus.html`, `core/schedule.html` |
| T7 | Remove dead CSS | Medium | `css/style.css` |
| T8 | Increase `--text-lt` contrast | Low | `css/style.css` |
| T9 | Skip-to-content link + table `scope`/`caption` | Low | All 22 HTML files, `css/style.css`, `tests/test_unit_html_structure.py` |
| T10 | SEO/social meta, favicon, robots/sitemap, security headers | Low (deferred) | N/A until hosting exists |

**Recommended execution order:** T1 → T3 → T2 → T6 → T5 → T4 → T7 → T9 → T8, running `pytest tests/ -v` after each. T10 stays parked until a hosting decision is made.
