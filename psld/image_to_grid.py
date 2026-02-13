from __future__ import annotations

from collections import Counter, deque


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{r:02X}{g:02X}{b:02X}"


def _components_by_color(cells: list[list[int | None]]) -> list[tuple[int, list[tuple[int, int]]]]:
    h = len(cells)
    w = len(cells[0]) if h else 0
    seen = [[False for _ in range(w)] for _ in range(h)]
    comps: list[tuple[int, list[tuple[int, int]]]] = []

    for y in range(h):
        for x in range(w):
            c = cells[y][x]
            if c is None or seen[y][x]:
                continue
            q: deque[tuple[int, int]] = deque()
            q.append((x, y))
            seen[y][x] = True
            pts: list[tuple[int, int]] = []
            while q:
                xx, yy = q.popleft()
                pts.append((xx, yy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = xx + dx, yy + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and cells[ny][nx] == c:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            comps.append((c, pts))

    return comps


def _denoise_small_components(
    cells: list[list[int | None]],
    *,
    min_component_size: int = 2,
    max_passes: int = 4,
) -> None:
    """
    Removes small single-tile/low-tile "noise" regions by recoloring them to the
    most common neighboring color. Deterministic (stable tie-break).
    """
    h = len(cells)
    w = len(cells[0]) if h else 0
    if h == 0 or w == 0:
        return

    for _ in range(max_passes):
        comps = _components_by_color(cells)
        small = [(c, pts) for (c, pts) in comps if len(pts) < min_component_size]
        if not small:
            return

        changed = False
        for c, pts in small:
            neighbor_colors: Counter[int] = Counter()
            for x, y in pts:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        nc = cells[ny][nx]
                        if nc is not None and nc != c:
                            neighbor_colors[nc] += 1
            if not neighbor_colors:
                continue

            # Deterministic: prefer most common; tie-break by smaller palette index.
            best_count = max(neighbor_colors.values())
            best = min(k for (k, v) in neighbor_colors.items() if v == best_count)
            for x, y in pts:
                cells[y][x] = best
                changed = True

        if not changed:
            return


def image_to_grid(
    path: str,
    *,
    w: int,
    h: int,
    colors: int = 5,
    alpha_threshold: int = 16,
    min_component_size: int = 2,
    background_hex: str = "#000000",
    fill_background: bool = False,
) -> tuple[list[str], list[list[int | None]]]:
    """
    Converts an input image to:
      - palette: list of "#RRGGBB"
      - cells: y-major grid of palette indices, or None for empty

    Requires Pillow, but imports it lazily so the rest of the package works without it.
    """
    try:
        from PIL import Image  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("Pillow is required for image_to_grid; install with: pip install '.[image]'") from e

    img = Image.open(path).convert("RGBA")

    # Downsample to the target grid deterministically (BOX = area average).
    small = img.resize((w, h), resample=Image.Resampling.BOX)

    # Create a working RGB image for quantization, with transparent pixels painted black.
    rgba = list(small.getdata())
    occ = []
    rgb = []
    for (r, g, b, a) in rgba:
        is_occ = a >= alpha_threshold
        occ.append(is_occ)
        rgb.append((r, g, b) if is_occ else (0, 0, 0))

    rgb_img = Image.new("RGB", (w, h))
    rgb_img.putdata(rgb)

    # Deterministic palette quantization.
    pal_img = rgb_img.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, kmeans=0)
    pal = pal_img.getpalette()  # list[int], length 768
    idxs = list(pal_img.getdata())

    # Build palette (only for actually-used indices on occupied cells).
    used = sorted({idxs[i] for i, is_occ in enumerate(occ) if is_occ})
    remap = {old: new for new, old in enumerate(used)}
    palette_hex: list[str] = []
    for old in used:
        r = pal[old * 3 + 0]
        g = pal[old * 3 + 1]
        b = pal[old * 3 + 2]
        palette_hex.append(_rgb_to_hex((r, g, b)))

    cells: list[list[int | None]] = [[None for _ in range(w)] for _ in range(h)]
    for y in range(h):
        for x in range(w):
            i = y * w + x
            if not occ[i]:
                cells[y][x] = None
            else:
                cells[y][x] = remap[idxs[i]]

    _denoise_small_components(cells, min_component_size=min_component_size)

    if fill_background:
        # Ensure there are no "empty" cells: transparency becomes a background color cell.
        # Normalize background to palette index 0 deterministically.
        bg = background_hex.upper()
        if bg in palette_hex:
            bg_old = palette_hex.index(bg)
            if bg_old != 0:
                # Swap palette entries and indices so bg becomes 0.
                palette_hex[0], palette_hex[bg_old] = palette_hex[bg_old], palette_hex[0]
                for y in range(h):
                    for x in range(w):
                        v = cells[y][x]
                        if v == 0:
                            cells[y][x] = bg_old
                        elif v == bg_old:
                            cells[y][x] = 0
        else:
            palette_hex.insert(0, bg)
            for y in range(h):
                for x in range(w):
                    if cells[y][x] is not None:
                        cells[y][x] = int(cells[y][x]) + 1

        for y in range(h):
            for x in range(w):
                if cells[y][x] is None:
                    cells[y][x] = 0

    return palette_hex, cells
