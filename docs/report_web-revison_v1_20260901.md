# Website Revision Report — theailab-net (IPHS 400)

**Date:** 2026-09-01
**Scope:** Full repository — 22 static HTML pages, shared stylesheet, pytest test suite, Netlify config, GitHub Actions CI
**Method:** Manual read of every page and config file, cross-file diffing (nav, dates, titles), grep-based audits for dead CSS/missing tags, and date-of-week verification against the 2026 calendar

## Executive Summary

This is a small, well-tested static site (22 HTML pages, one shared stylesheet, no build step) with a real pytest suite wired into CI/CD. The engineering discipline is good: the test suite genuinely catches broken links, missing structure, and nav drift, and it runs before every deploy. The site's actual weaknesses are in three places:

1. **One real content bug** — 5 of 15 week-page titles on the `Schedule` page don't match the destination page's own title/H1 (Weeks 6, 10, 13, 14, 15).
2. **A quiet DRY/maintainability problem** — the entire "Course Description" + "Learning Outcomes" block (3,538 characters) is duplicated verbatim between `about.html` and `syllabus.html`, and the assignment-weights table is duplicated between `syllabus.html` and `assignments.html`. Any future edit has to remember to touch both places, and the test suite won't catch drift between them.
3. **A stack of standard web best practices the site currently skips entirely**: no SEO/social meta tags, no favicon, no accessibility affordances beyond semantic HTML, no security headers beyond two, and a CI workflow that never runs on pull requests. None of these are urgent for a small course site, but several are one-line fixes with outsized payoff before the "Live site" URL goes into the README and gets shared with students.

Nothing here is structurally wrong — this is a punch list, not a rewrite.

---

## Findings

Findings are grouped by category and tagged with a rough severity: 🔴 High (visible bug / real risk), 🟡 Medium (best-practice gap worth fixing before launch), 🟢 Low (polish / nice-to-have).

### 1. Content Bugs

#### 🔴 1.1 — Schedule page link text doesn't match 5 of 15 week-page titles

`core/schedule.html` links to each week page using its own copy of the week's title as the link text. That copy has drifted from the actual `<title>`/`<h1>`/breadcrumb on the destination page for a third of the weeks:

| Week | `schedule.html` link text | Actual page title (`week-NN.html`) |
|---|---|---|
| 6 | "Hooks Architecture **and Guardrails**" | "Hooks Architecture" |
| 10 | "MP3 Demos and the Spec-Driven **Development** Landscape" | "MP3 Demos and the Spec-Driven Landscape" |
| 13 | "Full-Cycle Capstone Work Session **and MP4 Presentations**" | "Full-Cycle Capstone Work Session" |
| 14 | "Final Project Work Session **and Poster Development**" | "Final Project Work Session" |
| 15 | "Final Project **Poster** Presentations" | "Final Project Presentations" |

Every week page is internally consistent (its own `<title>`, hero `<h1>`, and breadcrumb all agree), so this is purely a Schedule-page copy issue, not a per-page one. The `<a href>` targets are all correct — the test suite (`test_schedule_links_to_all_15_weeks`) checks that link *targets* exist, not that link *text* matches the destination title, so this passes CI today undetected.

**Fix:** update the five link-text strings in `core/schedule.html` to match the destination pages (or reverse the fix if the longer titles are the intended ones — worth confirming with the instructor which version is authoritative, since the longer titles read as more complete). Consider adding a regression test (`test_schedule_link_text_matches_week_title`) that reads each week's `<h1>` and asserts the Schedule link text is identical, so this class of drift can't recur silently.

#### 🟡 1.2 — "Course Description" and "Learning Outcomes" duplicated verbatim between `about.html` and `syllabus.html`

The block from `<h2>Course Description</h2>` through the end of the outcomes list (3,538 characters, four paragraphs + a 9-item list) is byte-for-byte identical in both pages. Likewise, the assignment-weights table (weights, due dates) is duplicated between `syllabus.html` and `assignments.html`. With no build step and no templating, every future date change (and there will be several — the syllabus explicitly warns tools/dates will be revised mid-semester) has to be applied in two or three places by hand, and nothing in the test suite verifies the copies stay in sync.

**Fix options, roughly in order of effort:** (a) cheapest — leave the duplication but add a pytest check that diffs the shared blocks across pages and fails if they diverge; (b) trim `about.html` to a short summary + link to `syllabus.html#course-description` rather than repeating the whole block; (c) if the "no build step" constraint is negotiable, a tiny static-include step (even a pre-commit script that stamps shared fragments from one source file into both pages) would remove the risk entirely. Given the project's stated "no build step or JS framework" constraint, (a) or (b) fit best.

### 2. Markup / Consistency Issues

#### 🟡 2.1 — Inconsistent internal-link style within `core/` pages

`syllabus.html` and `schedule.html` link to sibling pages using the fully-qualified `../core/<page>.html` form (redundant but correct, since they're already inside `core/`), while `assignments.html`, `policies.html`, and `about.html` use the bare `<page>.html` form for the same links. Both resolve correctly and the test suite only checks that nav *labels* match a fixed set, not that hrefs follow one convention — so this passes CI, but it means the README's claim that "navigation is identical across all pages" is true for labels/targets but not for markup, and it signals these five pages weren't generated from one shared template/macro. Worth picking one convention (bare relative paths are simpler and match 3 of 5 pages already) and applying it uniformly.

#### 🟢 2.2 — Inconsistent attribute ordering on the active-nav-link marker

Most pages write `<a href="..." class="active">`, but `syllabus.html` and `schedule.html` write `<a class="active" href="...">`. Harmless (HTML attribute order never matters), but it's another small tell that the five `core/` pages weren't produced by one consistent process, worth normalizing.

#### 🟢 2.3 — GitHub repository URL is plain text, not a link

Both `core/about.html` ("Materials: `https://github.com/jon-chun/theailab-net`") and `core/syllabus.html` (Course Site row) render the repository URL inside a `<code>` tag instead of an `<a href>`. Students have to select-and-paste it manually. Worth wrapping in an anchor with `target="_blank" rel="noopener noreferrer"`.

#### 🟢 2.4 — README's "Live site" URL is still a placeholder

`README.md` line 13 reads `_add Netlify URL here once deployed_`. Expected pre-launch, but flagging since this report is being written the same day the repo says deployment is imminent — worth a note to update it (and the site's own `<meta>`/OG tags, see §3.1) once the Netlify site is live.

### 3. SEO / Discoverability

#### 🟡 3.1 — No meta description, Open Graph, or Twitter Card tags on any page

Zero pages have `<meta name="description">`, `og:title`/`og:description`/`og:image`, or Twitter Card tags. For a course site that will presumably be linked from Kenyon's course catalog, shared with prospective students, or posted in a syllabus repository search, this means link previews in Slack/Discord/email/social media render with no description and no image — just a bare title. A one-line `<meta name="description">` per page (and a shared `og:image`/`og:site_name` in a common partial, if one gets introduced) would fix this cheaply.

#### 🟡 3.2 — No favicon

No `<link rel="icon">` anywhere, and no favicon file in the repo. Browsers fall back to a blank/default tab icon, which reads as unfinished in a browser with many tabs open (a real scenario for students juggling this course site alongside Moodle, GitHub, and their agent CLI docs).

#### 🟢 3.3 — No `robots.txt` or `sitemap.xml`

Not urgent for a 22-page site (crawlers will find everything via the nav), but `sitemap.xml` costs little and helps search engines index week pages faster, and a `robots.txt` gives explicit control (e.g., if the instructor later wants search engines to skip a page).

### 4. Accessibility

#### 🟡 4.1 — No visible focus styling for keyboard navigation

`css/style.css` defines `:hover` states for links and nav items but no `:focus` / `:focus-visible` rule anywhere in the stylesheet. There's no `outline: none` reset either, so keyboard users aren't left with *zero* indicator (the browser default outline should still render), but the custom underline/color treatment used for `:hover` isn't mirrored for keyboard focus, so the experience is visually inconsistent between mouse and keyboard users. Recommend adding an explicit `:focus-visible` rule matching (or intentionally distinct from) the hover treatment, especially for `.main-nav a` and in-content links.

#### 🟡 4.2 — Active nav link isn't marked up for assistive tech

The current page in the nav is indicated only by a `class="active"` CSS hook (bold/underline styling). There's no `aria-current="page"` attribute, so screen-reader users get no equivalent signal for "this is the page you're on." This is a one-attribute fix per active link, across all 21 non-404 pages (candidate for a small script/find-replace rather than 21 manual edits).

#### 🟢 4.3 — No skip-to-content link

Every page repeats an identical 6-item nav before the main content. Keyboard and screen-reader users have no way to bypass it — they have to tab through Home/Syllabus/Schedule/Assignments/Policies/About on every single page load before reaching page content. A standard `<a class="skip-link" href="#main">Skip to content</a>` as the first focusable element (visually hidden until focused) is a well-established, cheap fix.

#### 🟢 4.4 — Data tables lack `scope` attributes and captions

The `<th>` cells in the Course Details, Assignments, Grading Scale, and Grading Rubric tables have no `scope="col"`/`scope="row"`, and no table has a `<caption>`. Screen readers can usually still infer simple header rows correctly, but explicit `scope` is the documented best practice for any table a sighted user would read by scanning row/column intersections (e.g., the grading rubric).

### 5. Security & Ops

#### 🟡 5.1 — CI workflow never runs on pull requests

`.github/workflows/deploy-netlify.yml` triggers only on `push: branches: [main]` and `workflow_dispatch`. There is no `pull_request` trigger. Practically, this means: if any contributor works on a feature branch and opens a PR before merging to `main`, the pytest suite (and thus the safety net this report just praised) never runs against that PR — it only runs *after* the merge, at which point the deploy job is already racing to push potentially-broken content live (the `test` job does gate `deploy` in the same run, so a broken push to `main` itself won't deploy, but a broken PR can be merged with a green checkmark that was never actually run). Given the repo is intended to host visible course changes throughout the semester with contributions likely reviewed via PR, adding:
```yaml
on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:
```
closes this gap and gives reviewers a CI status check on the PR itself.

#### 🟢 5.2 — Only two of the common security headers are set

`netlify.toml` sets `X-Frame-Options: DENY` and `X-Content-Type-Options: nosniff` for all routes, which is a reasonable baseline, but omits `Referrer-Policy`, `Permissions-Policy`, `Strict-Transport-Security`, and `Content-Security-Policy`. For a static, no-JS, no-form, no-cookie site the actual risk surface is small, but `Content-Security-Policy: default-src 'self'` and `Strict-Transport-Security: max-age=63072000; includeSubDomains` cost nothing to add and are standard practice for anything served over Netlify.

### 6. Dead / Unused CSS

#### 🟢 6.1 — Roughly 100+ lines of `style.css` are unreachable from any current page

`style.css` (620 lines) was adapted from a prior WordPress "Twenty Nineteen"-style course-blog theme, and it still carries the blog-specific machinery that theailab-net's plain syllabus-site pages never use:

- `.has-featured-image` / `.featured-media` (full-bleed duotone hero image variant) — every page uses `.no-featured-image` instead
- `.social-nav`
- `.badge`, `.badge-draft`, `.badge-private`, `.badge-placeholder`
- `.placeholder-notice` (and its own unit test, `test_no_placeholder_notice`, confirming it's intentionally never meant to appear)
- `.share-links`, `.post-nav`, `.entry-footer`, `.entry-meta`, `.post-preview`, `.other-blog-pages` (blog post chrome — this site has no blog/post pages)
- `.columns` (multi-column layout helper)
- `.wp-block-image`, `.wp-block-separator` (WordPress block-editor classes)

None of these selectors match any element in the 22 HTML pages (verified by grepping every class name against every page). This isn't a functional bug — dead CSS costs nothing at runtime beyond a fractionally larger stylesheet download — but it's a maintenance liability: a future editor reading `style.css` has no way to tell which rules are load-bearing and which are inherited cruft, and it invites accidental "fixes" to code nothing renders. Worth either deleting the unused blocks now, or (if the featured-image/blog layout is genuinely planned for later use, e.g. a future course-news/blog section) leaving a one-line comment at the top of each dead block saying so.

### 7. Test Suite Gaps

The existing suite (`test_unit_html_structure.py`, `test_integration_links.py`, `test_e2e_site.py`) is solid for what it covers — DOCTYPE, title suffix, stylesheet resolution, header/footer/hero presence, no leftover template branding, no placeholder text, internal link resolution, nav-label consistency, exact page count, and index-reachability. It does **not** currently check:

- 🟡 That Schedule-page link text matches the destination page's own title (would have caught §1.1 automatically)
- 🟢 That duplicated content blocks (about/syllabus, syllabus/assignments tables) stay in sync (would catch future drift from §1.2)
- 🟢 Presence of `meta name="description"`, favicon `<link>`, or `lang="en"` on `<html>` (the last of these is already correct on every page, but nothing pins it)
- 🟢 `aria-current="page"` / focus-visible CSS coverage (accessibility gaps in §4 have no automated check)
- 🟢 External-link hygiene (`target="_blank"` paired with `rel="noopener"`) — moot today since there are no external `<a>` links yet, but worth adding once §2.3 is fixed so it can't regress
- 🟢 HTML validity via a real parser/validator (the suite uses BeautifulSoup/lxml, which is lenient about malformed markup — a `html5lib`-strict pass or W3C validator run would catch structural issues BeautifulSoup silently repairs)

None of these are urgent additions, but §1.1 in particular shows the value of testing content *correspondence* between pages, not just link *existence* — the current suite would benefit from one or two tests in that direction.

---

## Prioritized Punch List

| # | Finding | Effort | Priority |
|---|---|---|---|
| 1 | Fix 5 mismatched week titles in `core/schedule.html` (§1.1) | Trivial (5 string edits) | Do first |
| 2 | Add `pull_request` trigger to CI workflow (§5.1) | Trivial (3-line YAML change) | Do first |
| 3 | Add favicon + meta description/OG tags (§3.1, §3.2) | Small | Before public launch |
| 4 | Add `aria-current="page"` to active nav links + `:focus-visible` styling (§4.1, §4.2) | Small | Before public launch |
| 5 | Reconcile internal-link style (`../core/x.html` vs `x.html`) across `core/` pages (§2.1) | Small | Housekeeping |
| 6 | Delete or comment-flag dead blog-template CSS (§6.1) | Small–Medium | Housekeeping |
| 7 | De-duplicate About/Syllabus content, or add a sync test (§1.2) | Medium | Before next major content edit |
| 8 | Add skip-link, table `scope` attributes, `robots.txt`/`sitemap.xml`, extra security headers (§4.3, §4.4, §3.3, §5.2) | Small each | Nice-to-have |

## What's Already Working Well

- Every page shares one stylesheet with no build step, exactly as documented in the README.
- The pytest suite is real, specific, and actually wired into CI as a gate before deploy — not a token test file.
- All 15 week pages' dates were independently verified against the actual 2026 calendar (Aug 27 = Thursday, Oct 8–9 break, Nov 21–29 Thanksgiving, etc.) — every single one is correct, including the two irregular single-session weeks (Week 1, Week 7).
- Prev/Next week navigation is correct end-to-end across all 15 week pages (Week 1 has no "prev," Week 15 has no "next," all others chain correctly).
- No leaked secrets, no leftover placeholder/Lorem-ipsum content, no broken internal links — the site is functionally complete and deployable today, with only the cosmetic issue above.
