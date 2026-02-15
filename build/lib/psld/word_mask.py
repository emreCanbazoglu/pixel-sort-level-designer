from __future__ import annotations

from .text_mask import scale_bitmap_to_grid


def _parse_ascii_bitmap(rows: list[str]) -> list[list[bool]]:
    if not rows:
        return [[False]]
    w = len(rows[0])
    if any(len(r) != w for r in rows):
        raise ValueError("Bitmap rows must be the same width")
    return [[ch == "#" for ch in row] for row in rows]


# 16x16 built-in silhouettes. These are intentionally simple "icon" shapes.
_TEMPLATES: dict[str, list[str]] = {
    # A simple cat-head silhouette (ears + head + eye holes). '.' is empty, '#' is filled.
    "CAT": [
        "........................",
        "......##........##......",
        ".....####......####.....",
        "....######....######....",
        "...########..########...",
        "..####################..",
        "..####################..",
        "..####################..",
        "..####################..",
        "..####################..",
        "..####################..",
        "..####################..",
        "...##################...",
        "...##################...",
        "....################....",
        ".....##############.....",
        "......############......",
        ".......##########.......",
        "........########........",
        ".........######.........",
        "..........####..........",
        "...........##...........",
        "........................",
        "........................",
    ],
}


def render_word_template_mask(
    word: str,
    *,
    w: int,
    h: int,
    padding: int = 1,
) -> list[list[bool]]:
    """
    Renders a known word into a silhouette mask (not literal letters).
    Falls back to a ValueError if the template is unknown.
    """
    key = word.strip().upper()
    if key not in _TEMPLATES:
        raise ValueError(f"Unknown template word: {word!r}. Known: {sorted(_TEMPLATES)}")

    src = _parse_ascii_bitmap(_TEMPLATES[key])
    return scale_bitmap_to_grid(src, w=w, h=h, padding=padding)
