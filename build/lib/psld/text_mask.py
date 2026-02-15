from __future__ import annotations

from dataclasses import dataclass


# Minimal built-in 5x7 font (uppercase A-Z, 0-9, space, dash).
# Each glyph is 7 rows of 5 bits, MSB on the left.
_GLYPHS: dict[str, list[int]] = {
    " ": [0b00000] * 7,
    "-": [0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000],
    "A": [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    "B": [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110],
    "C": [0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110],
    "D": [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110],
    "E": [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
    "F": [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000],
    "G": [0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01110],
    "H": [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    "I": [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b11111],
    "J": [0b11111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100],
    "K": [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001],
    "L": [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
    "M": [0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001],
    "N": [0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001],
    "O": [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    "P": [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
    "Q": [0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101],
    "R": [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
    "S": [0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110],
    "T": [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
    "U": [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    "V": [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100],
    "W": [0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b10101, 0b01010],
    "X": [0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001],
    "Y": [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100],
    "Z": [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111],
    "0": [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110],
    "1": [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    "2": [0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111],
    "3": [0b11110, 0b00001, 0b00001, 0b01110, 0b00001, 0b00001, 0b11110],
    "4": [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
    "5": [0b11111, 0b10000, 0b10000, 0b11110, 0b00001, 0b00001, 0b11110],
    "6": [0b01110, 0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
    "7": [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
    "8": [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
    "9": [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00001, 0b01110],
}


def _glyph_for(ch: str) -> list[int]:
    ch = ch.upper()
    if ch in _GLYPHS:
        return _GLYPHS[ch]
    return _GLYPHS["-"]


def render_text_bitmap(text: str, *, letter_spacing: int = 1) -> list[list[bool]]:
    """
    Renders text into a boolean bitmap using the built-in 5x7 font.
    Returns a y-major grid.
    """
    text = text.strip("\n")
    if not text:
        return [[False]]

    glyphs = [_glyph_for(ch) for ch in text]
    glyph_w = 5
    glyph_h = 7

    w = len(glyphs) * glyph_w + max(0, len(glyphs) - 1) * letter_spacing
    h = glyph_h

    out = [[False for _ in range(w)] for _ in range(h)]

    x0 = 0
    for g in glyphs:
        for y in range(glyph_h):
            row_bits = g[y]
            for x in range(glyph_w):
                bit = (row_bits >> (glyph_w - 1 - x)) & 1
                if bit:
                    out[y][x0 + x] = True
        x0 += glyph_w + letter_spacing

    return out


def scale_bitmap_to_grid(src: list[list[bool]], *, w: int, h: int, padding: int = 1) -> list[list[bool]]:
    """
    Nearest-neighbor scaling with optional padding inside the target grid.
    The source bitmap is centered in the target.
    """
    if w <= 0 or h <= 0:
        raise ValueError("Target grid must be positive")

    src_h = len(src)
    src_w = len(src[0]) if src_h else 0
    if src_h == 0 or src_w == 0:
        return [[False for _ in range(w)] for _ in range(h)]

    # Available area after padding.
    aw = max(1, w - 2 * padding)
    ah = max(1, h - 2 * padding)

    # Preserve aspect ratio by fitting to available area.
    scale_x = aw / src_w
    scale_y = ah / src_h
    scale = min(scale_x, scale_y)
    dst_w = max(1, int(round(src_w * scale)))
    dst_h = max(1, int(round(src_h * scale)))

    # Centered placement.
    off_x = (w - dst_w) // 2
    off_y = (h - dst_h) // 2

    out = [[False for _ in range(w)] for _ in range(h)]
    for dy in range(dst_h):
        sy = min(src_h - 1, int(dy / scale))
        for dx in range(dst_w):
            sx = min(src_w - 1, int(dx / scale))
            if src[sy][sx]:
                out[off_y + dy][off_x + dx] = True

    return out


def mask_to_ascii(mask: list[list[bool]]) -> str:
    return "\n".join("".join("#" if c else "." for c in row) for row in mask)

