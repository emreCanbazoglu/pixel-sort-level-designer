from __future__ import annotations

from collections import deque


def mask_from_strings(rows: list[str]) -> list[list[bool]]:
    if not rows:
        raise ValueError("mask rows empty")
    w = len(rows[0])
    if any(len(r) != w for r in rows):
        raise ValueError("mask rows must be same width")
    out: list[list[bool]] = []
    for r in rows:
        row: list[bool] = []
        for ch in r:
            if ch == "#":
                row.append(True)
            elif ch == ".":
                row.append(False)
            else:
                raise ValueError(f"invalid mask char: {ch!r}")
        out.append(row)
    return out


def _components(mask: list[list[bool]]) -> list[list[tuple[int, int]]]:
    h = len(mask)
    w = len(mask[0]) if h else 0
    seen = [[False for _ in range(w)] for _ in range(h)]
    comps: list[list[tuple[int, int]]] = []
    for y in range(h):
        for x in range(w):
            if not mask[y][x] or seen[y][x]:
                continue
            q: deque[tuple[int, int]] = deque([(x, y)])
            seen[y][x] = True
            pts: list[tuple[int, int]] = []
            while q:
                xx, yy = q.popleft()
                pts.append((xx, yy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = xx + dx, yy + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and mask[ny][nx]:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            comps.append(pts)
    return comps


def remove_small_foreground_components(mask: list[list[bool]], *, min_size: int = 2) -> list[list[bool]]:
    """
    Deterministically removes tiny foreground specks by turning them into background.
    Keeps the largest component regardless of size.
    """
    if min_size <= 1:
        return mask
    comps = _components(mask)
    if not comps:
        return mask
    comps.sort(key=lambda pts: (-len(pts), min(p[1] for p in pts), min(p[0] for p in pts)))
    keep = set(comps[0])
    out = [row[:] for row in mask]
    for pts in comps[1:]:
        if len(pts) < min_size:
            for x, y in pts:
                out[y][x] = False
        else:
            for x, y in pts:
                keep.add((x, y))
    return out

