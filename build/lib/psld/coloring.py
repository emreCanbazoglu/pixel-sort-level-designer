from __future__ import annotations

from .models import Grid


DEFAULT_PALETTE = [
    "#E63946",  # red
    "#457B9D",  # blue
    "#2A9D8F",  # teal
    "#F4A261",  # orange
    "#8D99AE",  # gray-blue
]


def colorize_mask(
    mask: list[list[bool]],
    *,
    palette_size: int = 4,
    mode: str = "solid",
) -> tuple[list[str], Grid]:
    """
    Assigns palette indices to occupied cells in a deterministic way.

    This is a placeholder for image quantization; it's used for text-driven levels
    and other mask-only sources.
    """
    h = len(mask)
    w = len(mask[0]) if h else 0
    if any(len(r) != w for r in mask):
        raise ValueError("mask must be rectangular")
    if palette_size <= 0:
        raise ValueError("palette_size must be positive")

    palette = DEFAULT_PALETTE[: max(1, min(palette_size, len(DEFAULT_PALETTE)))]
    k = len(palette)

    cells: list[list[int | None]] = [[None for _ in range(w)] for _ in range(h)]

    if mode == "solid":
        for y in range(h):
            for x in range(w):
                if mask[y][x]:
                    cells[y][x] = 0

    elif mode == "vertical_stripes":
        # Produces larger contiguous regions than checkerboards; still gives 2-5 colors.
        stripe_w = max(1, w // max(2, k))
        for y in range(h):
            for x in range(w):
                if mask[y][x]:
                    idx = (x // stripe_w) % k
                    cells[y][x] = idx

    elif mode == "quadrants":
        for y in range(h):
            for x in range(w):
                if mask[y][x]:
                    top = 0 if y < h // 2 else 1
                    left = 0 if x < w // 2 else 1
                    idx = (top * 2 + left) % k
                    cells[y][x] = idx

    else:
        raise ValueError(f"Unknown color mode: {mode}")

    return (palette, Grid(w=w, h=h, cells=cells))


def colorize_mask_filled(
    mask: list[list[bool]],
    *,
    palette_size: int = 4,
    mode: str = "vertical_stripes",
    background_index: int = 0,
) -> tuple[list[str], Grid]:
    """
    Like colorize_mask(), but guarantees there are no empty cells:
      - mask=False -> background_index
      - mask=True  -> one of the other colors

    This matches your "no empty cell; holes are a color" requirement.
    """
    h = len(mask)
    w = len(mask[0]) if h else 0
    if any(len(r) != w for r in mask):
        raise ValueError("mask must be rectangular")
    if palette_size <= 0:
        raise ValueError("palette_size must be positive")

    palette = DEFAULT_PALETTE[: max(1, min(palette_size, len(DEFAULT_PALETTE)))]
    k = len(palette)
    if not (0 <= background_index < k):
        raise ValueError("background_index out of range for palette")

    cells: list[list[int]] = [[background_index for _ in range(w)] for _ in range(h)]

    # Foreground indices exclude background if possible.
    fg = [i for i in range(k) if i != background_index]
    if not fg:
        return (palette, Grid(w=w, h=h, cells=cells))

    if mode == "solid":
        fill_idx = fg[0]
        for y in range(h):
            for x in range(w):
                if mask[y][x]:
                    cells[y][x] = fill_idx

    elif mode == "vertical_stripes":
        stripe_w = max(1, w // max(2, len(fg)))
        for y in range(h):
            for x in range(w):
                if mask[y][x]:
                    cells[y][x] = fg[(x // stripe_w) % len(fg)]

    elif mode == "quadrants":
        for y in range(h):
            for x in range(w):
                if mask[y][x]:
                    top = 0 if y < h // 2 else 1
                    left = 0 if x < w // 2 else 1
                    cells[y][x] = fg[(top * 2 + left) % len(fg)]

    else:
        raise ValueError(f"Unknown color mode: {mode}")

    return (palette, Grid(w=w, h=h, cells=cells))
