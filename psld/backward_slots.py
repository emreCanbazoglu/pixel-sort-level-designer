from __future__ import annotations

from .models import Pos


def _depth_fn(mask: list[list[bool]]):
    """
    Depth = Manhattan distance to the nearest empty cell or boundary in the four
    cardinal directions (higher = more interior).
    """
    h = len(mask)
    w = len(mask[0]) if h else 0
    cache: dict[tuple[int, int], int] = {}

    def depth(x: int, y: int) -> int:
        key = (x, y)
        if key in cache:
            return cache[key]
        if not mask[y][x]:
            cache[key] = 0
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

        cache[key] = best
        return best

    return depth


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
    Deterministic backward slot order for lane reachability.

    We compute a deterministic forward removal order by repeatedly removing an
    exposed slot (outer -> inner). The backward placement order is the reverse.
    """
    h = len(mask)
    if h == 0:
        raise ValueError("mask must be non-empty")
    w = len(mask[0])
    if any(len(r) != w for r in mask):
        raise ValueError("mask must be rectangular")

    present: set[tuple[int, int]] = {(x, y) for y in range(h) for x in range(w) if mask[y][x]}
    if not present:
        return []

    depth = _depth_fn(mask)

    forward: list[Pos] = []
    while present:
        row_min: list[int | None] = [None for _ in range(h)]
        row_max: list[int | None] = [None for _ in range(h)]
        col_min: list[int | None] = [None for _ in range(w)]
        col_max: list[int | None] = [None for _ in range(w)]

        # Compute extrema for the current present set.
        for (x, y) in present:
            mn = row_min[y]
            mx = row_max[y]
            row_min[y] = x if mn is None else min(mn, x)
            row_max[y] = x if mx is None else max(mx, x)

            mn = col_min[x]
            mx = col_max[x]
            col_min[x] = y if mn is None else min(mn, y)
            col_max[x] = y if mx is None else max(mx, y)

        # Pick an exposed slot deterministically: outer-most first (lowest depth), then top-left.
        best_xy: tuple[int, int] | None = None
        best_key: tuple[int, int, int] | None = None
        for (x, y) in present:
            if (
                row_min[y] == x
                or row_max[y] == x
                or col_min[x] == y
                or col_max[x] == y
            ):
                key = (int(depth(x, y)), y, x)
                if best_key is None or key < best_key:
                    best_key = key
                    best_xy = (x, y)

        if best_xy is None:
            # This should be impossible (any non-empty set has a row/col extremum),
            # but keep a hard error in case of a future bug.
            raise ValueError("Internal error: no exposed slot found for non-empty present set")

        x, y = best_xy
        forward.append(Pos(x=x, y=y))
        present.remove((x, y))

    # Backward (placement) order is reverse of forward removal.
    backward = list(reversed(forward))
    verify_forward_remove_order(mask, forward)
    return backward


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
