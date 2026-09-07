# Website Revision Report — theailab-net (IPHS 400)

**Date:** 2026-09-06
**Scope:** Full repository as it stands today — 22 static HTML pages, one shared stylesheet, the pytest test suite. `netlify.toml` and `.github/workflows/` were removed earlier today at the user's request; the site is now scoped as a standalone static site served locally (`python3 -m http.server`), with no deploy pipeline.
**Method:** Manual read of every HTML page, the stylesheet, the test suite, and the config/meta files; cross-file diffing (nav labels, hrefs, titles, duplicated content blocks); grep-based audits for dead CSS, missing tags, and unlinked plain-text URLs; re-verification of every finding from the prior report (`report_web-revison_v1_20260901.md`, 2026-09-01).

## Executive Summary

The site is small, clean, and functionally correct: no broken internal links, no leftover placeholder or template content, correct navigation and prev/next chaining across all 15 week pages, and a real pytest suite that runs actual assertions rather than smoke tests. Nothing here blocks the site from working today.

That said, a prior review five days ago (2026-09-01) already caught most of what's wrong, and **none of its findings have been fixed** — the schedule-page title mismatch, the duplicated content blocks, the inconsistent link style, and the missing accessibility/SEO affordances are all still present, byte-for-byte. This report:

1. **Re-verifies every open item from the 2026-09-01 report** against the current repo state (all still open — see the tracking table in §1).
2. **Flags one new, timely issue created by today's Netlify removal**: `404.html` was designed to be served via a Netlify redirect rule that no longer exists. Under `python3 -m http.server`, it is now completely unreachable in practice — a real regression relative to the site's stated behavior (§2).
3. **Adds several findings the prior report didn't cover**: a second and third instance of verbatim content duplication (`syllabus.html` ↔ `policies.html`, in addition to the already-known `syllabus.html` ↔ `about.html`/`assignments.html` duplication), and multiple plain-text institutional URLs/emails beyond the one GitHub link previously flagged (§3).
4. **Reframes priority** now that the "before public launch" framing no longer applies — this is explicitly a local-only, no-hosting site, so SEO/social-meta and HTTP security-header findings from the prior report drop in priority, while correctness, duplication, and the local-dev-specific 404 issue rise (§5).

Nothing here is structurally wrong. This remains a punch list, not a rewrite.

---

## 1. Carried-Over Findings — Status Check

Every finding from the 2026-09-01 report was individually re-verified against the current repository. All are still open:

| # | Finding (2026-09-01 report) | Status today | Verification |
|---|---|---|---|
| 1.1 | Schedule page link text doesn't match 5 of 15 week-page titles (Weeks 6, 10, 13, 14, 15) | **Still open** | Diffed `core/schedule.html` link text against each week's `<h1>`; all 5 mismatches unchanged |
| 1.2 | "Course Description"/"Learning Outcomes" duplicated verbatim, `about.html` ↔ `syllabus.html`; assignment-weights table duplicated, `syllabus.html` ↔ `assignments.html` | **Still open** | `diff` confirms byte-for-byte match; see also §3.1 below for a third duplicate block not previously reported |
| 2.1 | Inconsistent internal-link style within `core/` (`../core/x.html` vs. bare `x.html`) | **Still open** | `schedule.html`/`syllabus.html` use the verbose form; `about.html`/`assignments.html`/`policies.html` use the bare form |
| 2.2 | Inconsistent attribute order on `class="active"` markers | **Still open** | Same split as 2.1, same two files |
| 2.3 | GitHub repo URL is plain `<code>` text, not a link | **Still open**, and broader than reported (§3.2) | Confirmed in `about.html` and `syllabus.html`; several more unlinked URLs found this pass |
| 3.1 | No meta description / OG / Twitter Card tags anywhere | **Still open** | `grep` across all 22 pages: zero matches |
| 3.2 | No favicon | **Still open** | No `<link rel="icon">`, no favicon file in repo |
| 3.3 | No `robots.txt`/`sitemap.xml` | **Still open**, now lower priority (site is local-only; see §5) | Not present |
| 4.1 | No `:focus`/`:focus-visible` styling in `style.css` | **Still open** | Confirmed by reading the full stylesheet |
| 4.2 | Active nav link has no `aria-current="page"` | **Still open** | Only `class="active"`, no ARIA attribute, on any of the 21 non-404 pages |
| 4.3 | No skip-to-content link | **Still open** | Confirmed |
| 4.4 | Tables lack `scope`/`<caption>` | **Still open** | Confirmed on the Course Details, Assignments, Grading Scale, and Rubric tables |
| 5.1 | CI never ran on pull requests | **Moot** | `.github/workflows/` removed today; there is no CI to fix or misconfigure |
| 5.2 | Only 2 of ~5 common security headers set | **Moot** | `netlify.toml` removed today; headers are a hosting-layer concern that no longer applies to a local-only site |
| 6.1 | ~100+ lines of dead blog-template CSS | **Still open** | Re-ran the class-usage audit (see §4 below) — same set of unreferenced classes, none newly used |

Repeating the fix recommendations for these would just restate the 2026-09-01 report; they're summarized in the punch list (§6) and the original document remains the reference for suggested fixes. The rest of this report covers what's new or changed since then.

---

## 2. New Since 2026-09-01: The 404 Page Is Now Effectively Dead

`404.html` exists, passes every structural test, and is intentionally excluded from nav-consistency and reachability checks (`tests/conftest.py`'s `nav_pages` fixture documents this: *"404.html is a server-served fallback page... not linked from navigation or content"*). That design assumed a host that rewrites unmatched requests to it — which is exactly what the now-removed `netlify.toml` did:

```toml
[[redirects]]
  from = "/*"
  to = "/404.html"
  status = 404
```

With that config gone and the site now scoped to run only via `python3 -m http.server`, **there is no server-side mechanism left that serves `404.html` for a bad URL.** Python's `http.server` returns its own bare-bones "404 File not found" response for any missing path; it has no config surface for custom error pages. The consequence:

- `404.html` is dead code today — it will never actually be shown to a visitor of this site as currently run, despite existing, being tested, and being referenced as a deliberate feature.
- Separately, and worth fixing regardless of hosting: `404.html`'s own internal links (`href="index.html"`, `href="core/syllabus.html"`) are written relative to the *page's file location*, not the *site root*. If this page is ever again served via a catch-all rewrite (Netlify, Apache `ErrorDocument`, nginx `error_page`, GitHub Pages `404.html`, etc.) from a non-root URL — e.g., a request for `/weeks/nonexistent.html` — the browser resolves those relative links against `/weeks/`, producing `/weeks/index.html` and `/weeks/core/syllabus.html`, both of which don't exist. This bug was latent even under the old Netlify config and remains latent now; it just has no way to manifest with the current local-only setup.

**Recommendation:** Since the project brief is explicitly "local test webserver only, no deploy pipeline," the honest options are (a) delete `404.html` and its test coverage, documenting that the site has no working 404 mechanism in its current run mode, or (b) keep it as forward-looking scaffolding for whenever hosting is reintroduced, but fix its internal links to be root-relative (`/index.html`, `/core/syllabus.html`) so it's actually correct the next time a host redirects to it. Leaving it exactly as-is, silently untested against its one real usage scenario, is the one option that's actively misleading.

---

## 3. New Findings Not in the Prior Report

### 3.1 A third duplicated content block: "Secrets Hygiene and Agent Safety"

The prior report caught two duplication pairs (`about.html`↔`syllabus.html`, `syllabus.html`↔`assignments.html`). There is a third: the entire "Secrets Hygiene and Agent Safety" section — four bullet points, ~700 characters — appears verbatim in both `core/syllabus.html` (lines 85–92) and `core/policies.html` (lines 85–92). Same content, same heading, same bullet wording, in two files with no cross-reference between them.

This reinforces the underlying structural point from the prior report rather than adding a new category of problem: with no build step or include mechanism, this site has at least **three** independently-maintained copies of policy-critical text (course description/outcomes, the assignment-weights table, and now secrets-hygiene rules), each capable of silently drifting from the other two. A future edit to secrets policy — plausible, given the syllabus explicitly warns that "AI tooling changes on a timescale of weeks" — has two places to remember, with nothing in the test suite that would catch a missed one.

### 3.2 Several institutional references are plain text where a link was clearly intended

The prior report flagged one instance of this (`https://github.com/jon-chun/theailab-net` rendered in `<code>`, not `<a>`). Auditing every mention of an external resource across the site turns up more of the same pattern:

| Reference | Where | Current markup |
|---|---|---|
| `digital.kenyon.edu/dh` | `about.html`, `syllabus.html`, `policies.html`, `assignments.html` (4 mentions) | Plain text, sometimes bolded, never a link |
| `Moodle` / `Moodle.kenyon.edu` | `syllabus.html`, `about.html`, `assignments.html` | Plain text |
| `sass@kenyon.edu` | `policies.html` | Plain text, not even a `mailto:` link |
| `https://github.com/jon-chun/theailab-net` | `syllabus.html`, `about.html` | `<code>`, not `<a>` (previously reported) |

None of these are broken — they're just not clickable, which is a real usability cost on a page students are expected to act on (submit to Moodle, publish to digital.kenyon.edu, email SASS for accommodations). This is a pure omission, cheap to fix, and easy to miss precisely because each individual instance looks like "just some text" rather than a dead link.

### 3.3 Borderline text-contrast on `--text-lt`

`--text-lt: #767676` (used for the site tagline, breadcrumbs, page-meta, and footer text, mostly at 15–16px) against the `#fff` background computes to a contrast ratio of **~4.54:1** — just over the WCAG AA threshold (4.5:1) for normal text, but with essentially no margin. This isn't a finding the prior report's accessibility section covered (it focused on focus states, `aria-current`, skip links, and table semantics). It's not a failure today, but it's one rounding error or one slightly-off monitor/browser gamma away from becoming one, and it's used in several places simultaneously (footer, breadcrumbs, meta rows). Worth nudging to something with more headroom (e.g., `#5c5c5c`, ~5.9:1) rather than leaving it exactly at the line.

### 3.4 Test suite has no regression coverage for any of the above

Consistent with the prior report's §7 ("Test Suite Gaps"), none of the three new findings above are checked by the existing suite either:
- No test compares duplicated content blocks across files for drift (would have caught §3.1 the moment it was introduced).
- No test checks that a referenced external domain/email in body text is wrapped in an `<a>` (would catch §3.2-style regressions, admittedly a fuzzier check to write).
- No test asserts on `404.html`'s reachability story now that the hosting layer that made it reachable is gone — the existing `nav_pages` fixture *documents* the assumption ("404.html is a server-served fallback page") but nothing verifies that assumption still holds after `netlify.toml`'s removal. This is exactly the kind of silent invalidation that a comment can't protect against but a test could have flagged.

---

## 4. Dead CSS — Re-Verified

Re-ran the class-usage audit from the prior report's §6.1 (grep every CSS class selector in `style.css` against every `class="..."` attribute in all 22 HTML pages). The result is unchanged: the following selectors still match zero elements anywhere in the site —

`.has-featured-image`, `.featured-media` (and its `::after` duotone rule), `.social-nav`, `.badge` / `.badge-draft` / `.badge-private` / `.badge-placeholder`, `.placeholder-notice`, `.share-links`, `.post-nav`, `.entry-footer`, `.entry-meta`, `.post-preview`, `.other-blog-pages`, `.columns`, `.wp-block-image`, `.wp-block-separator`, and — newly confirmed this pass — `.page-meta` (defined in the stylesheet, referenced nowhere).

This is roughly a fifth of the 620-line stylesheet with no live caller. Not a functional bug, but the risk the prior report named still applies: a future editor has no signal for which rules are load-bearing.

---

## 5. Priority Reframing for a Local-Only Site

The user's direction today — strip Netlify/CI, run via `python3 -m http.server` only, no deploy pipeline — changes what "before launch" means for this project, because there is no launch in the hosted sense anymore. Re-scoring the punch list against that:

- **Drops in priority:** meta description/OG/Twitter Card tags (§3.1 of the old report), `robots.txt`/`sitemap.xml`, and HTTP security headers. These matter for a page indexed by search engines or shared as a rich link preview; a site that only ever runs on `localhost` for local viewing/grading has no audience for them. Worth doing eventually if the site is ever hosted again, but not a local-dev priority.
- **Unchanged priority — these are correctness/maintainability issues regardless of hosting:** the schedule-title mismatch (§1.1), all three duplicated-content pairs (§1.2 + §3.1 here), the inconsistent link style (§2.1/2.2), dead CSS (§4), and the missing content-drift tests (§3.4 here / §7 of the prior report).
- **Newly relevant because of today's change:** the `404.html` reachability problem (§2 here) — this is a direct, causal consequence of removing `netlify.toml`, not a pre-existing issue that happens to still apply.
- **Still worth doing, low effort regardless of hosting:** `aria-current="page"`, `:focus-visible` styling, skip link, table `scope` attributes, and linking the plain-text institutional URLs (§3.2) — these are about the experience of anyone using the site locally (instructor, students, TAs testing it before it's ever hosted anywhere), not about search engines or CDNs.

---

## 6. Prioritized Punch List

| # | Finding | New or carried over | Effort | Priority |
|---|---|---|---|---|
| 1 | Decide `404.html`'s fate: delete it, or fix its links to be root-relative and keep it as forward scaffolding (§2) | New | Trivial–Small | Do first |
| 2 | Fix 5 mismatched week titles in `core/schedule.html` | Carried over (§1.1) | Trivial | Do first |
| 3 | Add `aria-current="page"` to active nav links; add `:focus-visible` styling | Carried over (§4.1/4.2) | Small | Before next content pass |
| 4 | Link the plain-text institutional URLs/email (`digital.kenyon.edu/dh`, Moodle, `sass@kenyon.edu`, GitHub repo) (§3.2) | New (extends 2.3) | Small | Before next content pass |
| 5 | Reconcile `../core/x.html` vs. bare `x.html` link style across `core/` pages | Carried over (§2.1/2.2) | Small | Housekeeping |
| 6 | Add a pytest check that diffs the three known duplicated blocks (course description/outcomes, assignment-weights table, secrets-hygiene section) across their file pairs and fails on drift (§3.1, §3.4) | New scope on carried-over idea | Small–Medium | Before next content edit to any of the 4 affected pages |
| 7 | Delete or comment-flag dead blog-template CSS, including newly-confirmed `.page-meta` | Carried over (§6.1) | Small–Medium | Housekeeping |
| 8 | Nudge `--text-lt` to a color with more contrast headroom (§3.3) | New | Trivial | Nice-to-have |
| 9 | Add skip-link, table `scope` attributes | Carried over (§4.3/4.4) | Small | Nice-to-have |
| — | Meta description/OG tags, favicon, `robots.txt`/`sitemap.xml`, HTTP security headers | Carried over (§3.1–3.3, 5.2 of old report) | — | **Deprioritized** — only relevant if the site is hosted again |

## What's Already Working Well

- Zero broken internal links across all 22 pages; nav labels and targets are consistent everywhere they're tested.
- All 15 week pages' dates remain correct against the 2026 academic calendar; prev/next chaining is correct end-to-end (Week 1 has no "prev," Week 15 has no "next").
- No leaked secrets, no leftover placeholder/template text, no `Lorem ipsum`/`TBD`/`TODO` strings.
- The pytest suite (`tests/`) still runs clean and covers real structural invariants — DOCTYPE, title suffix, stylesheet resolution, header/footer/hero presence, link resolution, nav consistency, exact page/file counts, and index-reachability.
- Removing `netlify.toml` and `.github/workflows/` today was a clean cut: nothing in the remaining site (page content, tests, or README) depended on either file beyond the README's own deployment section, which was updated in the same change.
