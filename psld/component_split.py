from __future__ import annotations

import math


def _components_by_color(cells: list[list[int | None]]) -> list[tuple[int, list[tuple[int, int]]]]:
    # Local copy (kept small) to avoid circular imports.
    from collections import deque

    h = len(cells)
    w = len(cells[0]) if h else 0
    seen = [[False for _ in range(w)] for _ in range(h)]
    out: list[tuple[int, list[tuple[int, int]]]] = []

    for y in range(h):
        for x in range(w):
            c = cells[y][x]
            if c is None or seen[y][x]:
                continue
            q: deque[tuple[int, int]] = deque([(x, y)])
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
            out.append((int(c), pts))
    return out


def split_large_components(
    cells: list[list[int | None]],
    *,
    palette_size: int,
    max_component_size: int,
    mode: str = "sectors",  # "sectors" | "stripes_x" | "stripes_y" | "cuts"
    cut_thickness: int = 1,
    max_splits: int = 12,
    only_color: int | None = None,
) -> None:
    """
    Deterministically split oversized connected components by recoloring parts of them
    using other palette indices.

    This is intentionally simple and purely deterministic. It does not "invent" pixels;
    it only reassigns palette indices within already-occupied cells.
    """
    if max_component_size <= 0:
        raise ValueError("max_component_size must be positive")
    if cut_thickness <= 0:
        raise ValueError("cut_thickness must be positive")
    if palette_size < 2:
        return
    h = len(cells)
    w = len(cells[0]) if h else 0
    if h == 0 or w == 0:
        return
    if any(len(r) != w for r in cells):
        raise ValueError("cells must be rectangular")

    comps = _components_by_color(cells)
    for color, pts in comps:
        if only_color is not None and color != int(only_color):
            continue
        n = len(pts)
        if n <= max_component_size:
            continue

        # How many chunks do we want this component split into?
        splits = (n + max_component_size - 1) // max_component_size
        splits = max(2, min(int(splits), max_splits))
        if splits <= 1:
            continue

        # Deterministic color assignment cycle, starting with the original color.
        color_cycle = [color] + [i for i in range(palette_size) if i != color]
        if not color_cycle:
            continue

        if mode == "sectors":
            cx = sum(x for x, _ in pts) / n
            cy = sum(y for _, y in pts) / n
            for x, y in pts:
                theta = math.atan2(y - cy, x - cx)  # [-pi, pi]
                t = (theta + math.pi) / (2 * math.pi)  # [0,1]
                b = int(t * splits)  # [0, splits-1] (pi edge maps to splits; clamp)
                if b >= splits:
                    b = splits - 1
                cells[y][x] = color_cycle[b % len(color_cycle)]

        elif mode == "stripes_x":
            xs = [x for x, _ in pts]
            minx, maxx = min(xs), max(xs)
            span = max(1, maxx - minx + 1)
            for x, y in pts:
                t = (x - minx) / span
                b = int(t * splits)
                if b >= splits:
                    b = splits - 1
                cells[y][x] = color_cycle[b % len(color_cycle)]

        elif mode == "stripes_y":
            ys = [y for _, y in pts]
            miny, maxy = min(ys), max(ys)
            span = max(1, maxy - miny + 1)
            for x, y in pts:
                t = (y - miny) / span
                b = int(t * splits)
                if b >= splits:
                    b = splits - 1
                cells[y][x] = color_cycle[b % len(color_cycle)]

        elif mode == "cuts":
            # Prefer inserting thin seams (few recolored cells) to preserve readability.
            # We do up to (splits-1) cuts; each cut recolors a line within the component.
            pts_set = set(pts)

            def is_boundary(p: tuple[int, int]) -> bool:
                x, y = p
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if (x + dx, y + dy) not in pts_set:
                        return True
                return False

            # Try to keep the component's boundary color intact (outline readability).
            interior = [p for p in pts if not is_boundary(p)]
            use_pts = interior if interior else pts
            use_set = set(use_pts)

            xs = [x for x, _ in use_pts]
            ys = [y for _, y in use_pts]
            minx, maxx = min(xs), max(xs)
            miny, maxy = min(ys), max(ys)

            # Alternate cut orientation; choose line with most cells to maximize split chance.
            for cut_i in range(splits - 1):
                sep_color = color_cycle[(1 + cut_i) % len(color_cycle)]

                if (cut_i % 2) == 0:
                    # Vertical cut near median x.
                    mid = sorted(xs)[len(xs) // 2]
                    best_x = None
                    best_cnt = -1
                    # Search outward from mid for a good cut line.
                    for dx in range(0, maxx - minx + 1):
                        for x0 in (mid - dx, mid + dx):
                            if x0 < minx or x0 > maxx:
                                continue
                            cnt = sum(1 for (x, y) in use_pts if x == x0)
                            if cnt > best_cnt:
                                best_cnt = cnt
                                best_x = x0
                        if best_cnt >= 3:
                            break
                    if best_x is None or best_cnt <= 0:
                        continue
                    for t in range(cut_thickness):
                        xline = best_x + (t - (cut_thickness // 2))
                        for (x, y) in pts:
                            if x == xline and (x, y) in pts_set and (x, y) in use_set:
                                cells[y][x] = sep_color
                else:
                    # Horizontal cut near median y.
                    mid = sorted(ys)[len(ys) // 2]
                    best_y = None
                    best_cnt = -1
                    for dy in range(0, maxy - miny + 1):
                        for y0 in (mid - dy, mid + dy):
                            if y0 < miny or y0 > maxy:
                                continue
                            cnt = sum(1 for (x, y) in use_pts if y == y0)
                            if cnt > best_cnt:
                                best_cnt = cnt
                                best_y = y0
                        if best_cnt >= 3:
                            break
                    if best_y is None or best_cnt <= 0:
                        continue
                    for t in range(cut_thickness):
                        yline = best_y + (t - (cut_thickness // 2))
                        for (x, y) in pts:
                            if y == yline and (x, y) in pts_set and (x, y) in use_set:
                                cells[y][x] = sep_color

        else:
            raise ValueError(f"Unknown split mode: {mode}")
