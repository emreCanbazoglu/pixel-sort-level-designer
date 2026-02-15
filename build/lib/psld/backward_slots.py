from __future__ import annotations

from dataclasses import dataclass

from .models import Pos


def _row_extrema(present: set[tuple[int, int]], y: int) -> tuple[int, int] | None:
    xs = [x for (x, yy) in present if yy == y]
    if not xs:
        return None
    return (min(xs), max(xs))


def _col_extrema(present: set[tuple[int, int]], x: int) -> tuple[int, int] | None:
    ys = [y for (xx, y) in present if xx == x]
    if not ys:
        return None
    return (min(ys), max(ys))


def is_exposed(mask: list[list[bool]], present: set[tuple[int, int]], p: Pos) -> bool:
    """
    Exposure = lane-reachable from at least one side (left/right or top/bottom),
    given the currently present slots.

    For a given row y:
      - reachable from left iff x is the min occupied x in that row
      - reachable from right iff x is the max occupied x in that row

    For a given column x:
      - reachable from top iff y is the min occupied y in that column
      - reachable from bottom iff y is the max occupied y in that column
    """
    if not mask[p.y][p.x]:
        return False
    if (p.x, p.y) not in present:
        return False

    row = _row_extrema(present, p.y)
    if row is not None and (p.x == row[0] or p.x == row[1]):
        return True

    col = _col_extrema(present, p.x)
    if col is not None and (p.y == col[0] or p.y == col[1]):
        return True

    return False


def generate_backward_place_order(mask: list[list[bool]]) -> list[Pos]:
    """
    Deterministic backward slot generator.

    Starts from an empty solved board (no slots present) and *adds* slots
    (inner -> outer) such that each newly-added slot is lane-reachable
    at placement time (i.e., exposed) when considered with the already-placed slots.

    The forward playable clearing order is simply the reverse of this list.

    If generation fails, the mask cannot be assigned a strict outer->inner reachable
    order under the lane reachability rules.
    """
    h = len(mask)
    if h == 0:
        raise ValueError("mask must be non-empty")
    w = len(mask[0])
    if any(len(r) != w for r in mask):
        raise ValueError("mask must be rectangular")

    remaining: set[tuple[int, int]] = {(x, y) for y in range(h) for x in range(w) if mask[y][x]}
    present: set[tuple[int, int]] = set()

    order: list[Pos] = []

    # Deterministic tie-break: choose the candidate with the largest "depth" (more interior)
    # computed against the original mask, then lowest (y, x).
    depth_cache: dict[tuple[int, int], int] = {}

    def depth(x: int, y: int) -> int:
        # Manhattan distance to the nearest empty cell or boundary in 4-neighborhood directions.
        # Higher = more interior. Purely a tie-breaker; correctness comes from exposure checks.
        key = (x, y)
        if key in depth_cache:
            return depth_cache[key]

        if not mask[y][x]:
            depth_cache[key] = 0
            return 0

        best = 10**9
        # left
        d = 0
        xx = x
        while True:
            xx -= 1
            d += 1
            if xx < 0 or not mask[y][xx]:
                best = min(best, d)
                break
        # right
        d = 0
        xx = x
        while True:
            xx += 1
            d += 1
            if xx >= w or not mask[y][xx]:
                best = min(best, d)
                break
        # up
        d = 0
        yy = y
        while True:
            yy -= 1
            d += 1
            if yy < 0 or not mask[yy][x]:
                best = min(best, d)
                break
        # down
        d = 0
        yy = y
        while True:
            yy += 1
            d += 1
            if yy >= h or not mask[yy][x]:
                best = min(best, d)
                break

        depth_cache[key] = best
        return best

    while remaining:
        candidates: list[tuple[int, int]] = []
        # A slot is valid to add now if it would be exposed after being added.
        for (x, y) in remaining:
            tmp_present = present | {(x, y)}
            if is_exposed(mask, tmp_present, Pos(x=x, y=y)):
                candidates.append((x, y))

        if not candidates:
            # Provide a small debug hint.
            raise ValueError(
                "No reachable slot placement found; mask likely violates lane-reachability layering"
            )

        # Choose deterministically: prefer more interior, then top-left.
        candidates.sort(key=lambda xy: (-depth(xy[0], xy[1]), xy[1], xy[0]))
        x, y = candidates[0]

        present.add((x, y))
        remaining.remove((x, y))
        order.append(Pos(x=x, y=y))

    return order


def verify_forward_remove_order(mask: list[list[bool]], forward_order: list[Pos]) -> None:
    """
    Verifies that each removal step is valid (the removed slot is exposed at that time).
    Raises ValueError on the first invalid step.
    """
    h = len(mask)
    w = len(mask[0]) if h else 0

    present = {(x, y) for y in range(h) for x in range(w) if mask[y][x]}

    for i, p in enumerate(forward_order):
        if (p.x, p.y) not in present:
            raise ValueError(f"Step {i}: removing a slot not present at {p}")
        if not is_exposed(mask, present, p):
            raise ValueError(f"Step {i}: slot not exposed/reachable at removal time: {p}")
        present.remove((p.x, p.y))

    if present:
        raise ValueError("Forward order ended early; slots remain present")

