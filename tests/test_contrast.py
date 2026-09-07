"""Test that muted/secondary text color tokens meet WCAG AA contrast (4.5:1)
against the page background, with real margin rather than sitting on the line."""
import re
from pathlib import Path

SITE_ROOT = Path(__file__).parent.parent

# Require meaningfully more headroom than the bare 4.5:1 AA minimum, so small
# rendering differences (gamma, zoom rounding) can't tip it under.
MIN_CONTRAST_RATIO = 5.0


def _expand_hex(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(ch * 2 for ch in hex_color)
    return hex_color


def _srgb_channel_to_linear(c):
    c = c / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_color):
    hex_color = _expand_hex(hex_color)
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (_srgb_channel_to_linear(c) for c in (r, g, b))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(hex_a, hex_b):
    la, lb = _relative_luminance(hex_a), _relative_luminance(hex_b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def test_text_lt_has_contrast_headroom_against_background():
    css = (SITE_ROOT / "css" / "style.css").read_text(encoding="utf-8")
    bg_match = re.search(r"--bg:\s*(#[0-9a-fA-F]{3,6})", css)
    text_lt_match = re.search(r"--text-lt:\s*(#[0-9a-fA-F]{3,6})", css)
    assert bg_match and text_lt_match, "Could not find --bg / --text-lt tokens in css/style.css"

    ratio = _contrast_ratio(bg_match.group(1), text_lt_match.group(1))
    assert ratio >= MIN_CONTRAST_RATIO, (
        f"--text-lt ({text_lt_match.group(1)}) against --bg ({bg_match.group(1)}) "
        f"has only {ratio:.2f}:1 contrast; need at least {MIN_CONTRAST_RATIO}:1 headroom"
    )
