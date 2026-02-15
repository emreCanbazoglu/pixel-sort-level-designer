from __future__ import annotations

import json


def level_json_to_png(
    level_path: str,
    *,
    out_path: str,
    layer: str = "slots",  # or "top"
    scale: int = 16,
    draw_grid: bool = True,
) -> None:
    """
    Renders a level JSON (palette + grid) to a PNG for fast visual iteration.

    Requires Pillow, but imports lazily so text-only workflows don't break.
    """
    try:
        from PIL import Image, ImageDraw  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("Pillow is required for PNG rendering; install with: pip install '.[image]'") from e

    d = json.load(open(level_path, "r", encoding="utf-8"))
    palette: list[str] = d["palette"]
    grid = d[layer]
    h = len(grid)
    w = len(grid[0]) if h else 0

    def hex_to_rgb(hx: str) -> tuple[int, int, int]:
        hx = hx.strip()
        if hx.startswith("#"):
            hx = hx[1:]
        return (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16))

    # Transparent for empty cells.
    img = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for y in range(h):
        for x in range(w):
            v = grid[y][x]
            if v is None:
                continue
            rgb = hex_to_rgb(palette[int(v)])
            x0, y0 = x * scale, y * scale
            draw.rectangle([x0, y0, x0 + scale - 1, y0 + scale - 1], fill=rgb + (255,))

    if draw_grid and scale >= 6:
        # Light grid lines.
        for x in range(w + 1):
            xx = x * scale
            draw.line([(xx, 0), (xx, h * scale)], fill=(0, 0, 0, 40), width=1)
        for y in range(h + 1):
            yy = y * scale
            draw.line([(0, yy), (w * scale, yy)], fill=(0, 0, 0, 40), width=1)

    img.save(out_path, format="PNG")


def level_json_to_composite_png(
    level_path: str,
    *,
    out_path: str,
    scale: int = 16,
    inset_scale: int | None = None,
    inset_alpha: int = 255,
    draw_grid: bool = True,
    draw_inset_outline: bool = False,
) -> None:
    """
    Renders a composite PNG:
    - bottom layer (slots) as full-size cells
    - top layer as smaller inset cells centered within each occupied cell
    """
    try:
        from PIL import Image, ImageDraw  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("Pillow is required for PNG rendering; install with: pip install '.[image]'") from e

    d = json.load(open(level_path, "r", encoding="utf-8"))
    palette: list[str] = d["palette"]
    slots = d["slots"]
    top = d["top"]
    h = len(slots)
    w = len(slots[0]) if h else 0

    if inset_scale is None:
        inset_scale = max(2, int(scale * 0.6))
    inset_scale = max(2, min(int(inset_scale), int(scale)))
    inset_alpha = max(0, min(int(inset_alpha), 255))

    def hex_to_rgb(hx: str) -> tuple[int, int, int]:
        hx = hx.strip()
        if hx.startswith("#"):
            hx = hx[1:]
        return (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16))

    img = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw slots as base.
    for y in range(h):
        for x in range(w):
            v = slots[y][x]
            if v is None:
                continue
            rgb = hex_to_rgb(palette[int(v)])
            x0, y0 = x * scale, y * scale
            draw.rectangle([x0, y0, x0 + scale - 1, y0 + scale - 1], fill=rgb + (255,))

    # Draw top as inset.
    pad = (scale - inset_scale) // 2
    for y in range(h):
        for x in range(w):
            v = top[y][x]
            if v is None:
                continue
            rgb = hex_to_rgb(palette[int(v)])
            x0, y0 = x * scale + pad, y * scale + pad
            x1, y1 = x0 + inset_scale - 1, y0 + inset_scale - 1
            draw.rectangle([x0, y0, x1, y1], fill=rgb + (inset_alpha,))
            if draw_inset_outline and inset_scale >= 4:
                draw.rectangle([x0, y0, x1, y1], outline=(0, 0, 0, 90), width=1)

    if draw_grid and scale >= 6:
        for x in range(w + 1):
            xx = x * scale
            draw.line([(xx, 0), (xx, h * scale)], fill=(0, 0, 0, 40), width=1)
        for y in range(h + 1):
            yy = y * scale
            draw.line([(0, yy), (w * scale, yy)], fill=(0, 0, 0, 40), width=1)

    img.save(out_path, format="PNG")
