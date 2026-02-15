from __future__ import annotations


def normalize_hex_palette(palette: list[str]) -> list[str]:
    out: list[str] = []
    for hx in palette:
        s = hx.strip()
        if not s:
            continue
        if not s.startswith("#"):
            s = "#" + s
        s = s.upper()
        if len(s) != 7 or any(ch not in "0123456789ABCDEF#" for ch in s):
            raise ValueError(f"Invalid hex color: {hx!r} (expected '#RRGGBB')")
        out.append(s)
    if not out:
        raise ValueError("palette must contain at least one color")
    return out


def hex_to_rgb(hx: str) -> tuple[int, int, int]:
    s = hx.strip()
    if s.startswith("#"):
        s = s[1:]
    if len(s) != 6:
        raise ValueError(f"Invalid hex color: {hx!r}")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def luma_709(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def map_rgb_to_palette_nearest(rgb: tuple[int, int, int], palette_rgb: list[tuple[int, int, int]]) -> int:
    """
    Deterministic nearest-color mapping in RGB space (squared distance).
    Tie-break: lowest palette index.
    """
    r, g, b = rgb
    best_i = 0
    best_d = 10**18
    for i, (pr, pg, pb) in enumerate(palette_rgb):
        d = (r - pr) * (r - pr) + (g - pg) * (g - pg) + (b - pb) * (b - pb)
        if d < best_d:
            best_d = d
            best_i = i
    return best_i


def map_rgb_to_palette_luma_bucket(
    rgb: tuple[int, int, int],
    *,
    palette_rgb: list[tuple[int, int, int]],
    palette_by_luma: list[int],
    min_l: float,
    max_l: float,
) -> int:
    """
    Map based on pixel luminance bucket across the palette (sorted by palette luminance).
    Output is the palette index in the original palette order.
    """
    k = len(palette_rgb)
    if k <= 0:
        raise ValueError("palette_rgb empty")
    if k == 1:
        return 0
    l = luma_709(rgb)
    if max_l <= min_l:
        # Degenerate: map to the closest palette entry by luminance.
        best_i = 0
        best_d = 10**18
        for i, prgb in enumerate(palette_rgb):
            d = abs(luma_709(prgb) - l)
            if d < best_d:
                best_d = d
                best_i = i
        return best_i

    t = (l - min_l) / (max_l - min_l)
    if t < 0.0:
        t = 0.0
    if t > 1.0:
        t = 1.0
    b = int(t * (k - 1) + 1e-9)  # floor into [0, k-1]
    if b < 0:
        b = 0
    if b >= k:
        b = k - 1
    return int(palette_by_luma[b])

