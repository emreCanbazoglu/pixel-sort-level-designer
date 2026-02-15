from __future__ import annotations

from dataclasses import dataclass

from .component_split import split_large_components


@dataclass(frozen=True, slots=True)
class RebalanceResult:
    cells: list[list[int | None]]
    ok: bool
    iterations: int
    dominant_color: int | None
    dominant_share: float


def _counts(cells: list[list[int | None]]) -> tuple[int, dict[int, int]]:
    occ = 0
    by: dict[int, int] = {}
    for row in cells:
        for c in row:
            if c is None:
                continue
            occ += 1
            by[int(c)] = by.get(int(c), 0) + 1
    return occ, by


def _component_sizes_for_color(cells: list[list[int | None]], color: int) -> list[int]:
    from collections import deque

    h = len(cells)
    w = len(cells[0]) if h else 0
    seen = [[False for _ in range(w)] for _ in range(h)]
    sizes: list[int] = []
    for y in range(h):
        for x in range(w):
            if seen[y][x] or cells[y][x] != color:
                continue
            q: deque[tuple[int, int]] = deque([(x, y)])
            seen[y][x] = True
            n = 0
            while q:
                xx, yy = q.popleft()
                n += 1
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = xx + dx, yy + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and cells[ny][nx] == color:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            sizes.append(n)
    sizes.sort(reverse=True)
    return sizes


def rebalance_top_for_derangement(
    top_cells: list[list[int | None]],
    *,
    palette_size: int,
    max_dominant_share: float = 0.5,
    max_iters: int = 6,
    split_mode: str = "cuts",
    cut_thickness: int = 2,
) -> RebalanceResult:
    """
    Try to make derangement feasible by reducing any dominant color share to <= max_dominant_share.

    This does a minimal visual intervention: insert a few deterministic seams into the dominant
    color's largest component by reusing split_large_components(mode='cuts').
    """
    if not (0.0 < max_dominant_share <= 1.0):
        raise ValueError("max_dominant_share must be in (0, 1]")

    cells = [row[:] for row in top_cells]
    occ, by = _counts(cells)
    if occ == 0:
        return RebalanceResult(cells=cells, ok=True, iterations=0, dominant_color=None, dominant_share=0.0)
    if not by:
        return RebalanceResult(cells=cells, ok=True, iterations=0, dominant_color=None, dominant_share=0.0)

    def dominant() -> tuple[int, int]:
        # deterministic tie-break: smaller color index
        best_c = min(by)
        best_n = by[best_c]
        for c, n in by.items():
            if n > best_n or (n == best_n and c < best_c):
                best_c = c
                best_n = n
        return best_c, best_n

    iters = 0
    while True:
        dcol, dcnt = dominant()
        share = dcnt / occ
        if share <= max_dominant_share:
            return RebalanceResult(cells=cells, ok=True, iterations=iters, dominant_color=dcol, dominant_share=share)
        if iters >= max_iters:
            return RebalanceResult(cells=cells, ok=False, iterations=iters, dominant_color=dcol, dominant_share=share)

        # Insert one seam into the dominant color's largest component by forcing splits=2.
        # To keep the change minimal, try to target only the strictly-largest component.
        sizes = _component_sizes_for_color(cells, dcol)
        if not sizes:
            return RebalanceResult(cells=cells, ok=False, iterations=iters, dominant_color=dcol, dominant_share=share)
        largest = sizes[0]
        second = sizes[1] if len(sizes) > 1 else 0
        # Cut components > max_component_size. Setting it to `second` targets only the largest.
        max_component_size = second if second > 0 else max(1, largest // 2)

        split_large_components(
            cells,
            palette_size=palette_size,
            max_component_size=max_component_size,
            mode=split_mode,
            cut_thickness=cut_thickness,
            max_splits=2,  # exactly one cut per iteration
            only_color=dcol,
        )

        occ, by = _counts(cells)
        iters += 1
