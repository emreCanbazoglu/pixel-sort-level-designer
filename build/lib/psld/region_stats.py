from __future__ import annotations

from dataclasses import dataclass
from collections import Counter, deque


@dataclass(frozen=True, slots=True)
class ColorRegionStats:
    color_index: int
    regions: int
    total_cells: int
    largest: int
    smallest: int


@dataclass(frozen=True, slots=True)
class GridRegionStats:
    occupied_cells: int
    empty_cells: int
    total_regions: int
    colors: list[ColorRegionStats]  # sorted by color_index

    @property
    def fragmentation(self) -> float:
        """
        Heuristic: regions per occupied cell (lower is better).
        0.0 means empty grid.
        """
        if self.occupied_cells <= 0:
            return 0.0
        return self.total_regions / self.occupied_cells


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
            comps.append((int(c), pts))
    return comps


def analyze_grid_regions(cells: list[list[int | None]]) -> GridRegionStats:
    """
    Deterministic region analysis (4-neighborhood) per color index.
    """
    h = len(cells)
    w = len(cells[0]) if h else 0
    if h == 0 or w == 0:
        return GridRegionStats(occupied_cells=0, empty_cells=0, total_regions=0, colors=[])
    if any(len(r) != w for r in cells):
        raise ValueError("cells must be rectangular")

    empty = sum(1 for row in cells for c in row if c is None)
    occ = h * w - empty

    comps = _components_by_color(cells)

    by_color: dict[int, list[int]] = {}
    for c, pts in comps:
        by_color.setdefault(c, []).append(len(pts))

    color_stats: list[ColorRegionStats] = []
    for c in sorted(by_color):
        sizes = sorted(by_color[c])
        color_stats.append(
            ColorRegionStats(
                color_index=c,
                regions=len(sizes),
                total_cells=sum(sizes),
                largest=max(sizes) if sizes else 0,
                smallest=min(sizes) if sizes else 0,
            )
        )

    return GridRegionStats(
        occupied_cells=occ,
        empty_cells=empty,
        total_regions=len(comps),
        colors=color_stats,
    )


@dataclass(frozen=True, slots=True)
class ValidationResult:
    ok: bool
    reasons: list[str]
    stats: GridRegionStats


def validate_grid_regions(
    cells: list[list[int | None]],
    *,
    min_largest_region: int | None = None,
    max_total_regions: int | None = None,
    max_fragmentation: float | None = None,
    min_occupied_cells: int | None = None,
) -> ValidationResult:
    """
    Basic deterministic gating to avoid "confetti" boards.

    All thresholds are optional; only provided ones are enforced.
    """
    stats = analyze_grid_regions(cells)
    reasons: list[str] = []

    if min_occupied_cells is not None and stats.occupied_cells < min_occupied_cells:
        reasons.append(f"occupied_cells {stats.occupied_cells} < min_occupied_cells {min_occupied_cells}")

    if max_total_regions is not None and stats.total_regions > max_total_regions:
        reasons.append(f"total_regions {stats.total_regions} > max_total_regions {max_total_regions}")

    if max_fragmentation is not None and stats.fragmentation > max_fragmentation:
        reasons.append(f"fragmentation {stats.fragmentation:.4f} > max_fragmentation {max_fragmentation:.4f}")

    if min_largest_region is not None:
        # Enforce per-color largest region threshold (ignoring colors not present).
        for cs in stats.colors:
            if cs.largest < min_largest_region:
                reasons.append(
                    f"color {cs.color_index}: largest_region {cs.largest} < min_largest_region {min_largest_region}"
                )

    return ValidationResult(ok=not reasons, reasons=reasons, stats=stats)

