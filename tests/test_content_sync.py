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


def test_assignment_weights_table_matches_syllabus_and_assignments():
    syllabus = SITE_ROOT / "core" / "syllabus.html"
    assignments = SITE_ROOT / "core" / "assignments.html"
    start = "<h2>Summary of Assignments and Weights</h2>"
    end = '<tr><th scope="row">Total</th><th scope="row">100%</th><td></td></tr>\n</table>'
    block_syllabus = _normalize(_extract(syllabus, start, end))
    block_assignments = _normalize(_extract(assignments, start, end))
    assert block_syllabus == block_assignments, (
        "core/syllabus.html and core/assignments.html have drifted in the "
        "assignment-weights table. Update both to match."
    )


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
