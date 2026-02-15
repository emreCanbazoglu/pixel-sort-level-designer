from __future__ import annotations

from dataclasses import dataclass
from collections import deque


@dataclass(frozen=True, slots=True)
class Shooter:
    color: int
    ammo: int
    pos: int  # perimeter index [0, L)


@dataclass(frozen=True, slots=True)
class GameConfig:
    conveyor_capacity: int = 5
    entrance_pos: int = 0  # perimeter index where new shooters spawn
    move_then_fire: bool = True  # tick ordering


def perimeter_len(w: int, h: int) -> int:
    return 2 * w + 2 * h


def pos_to_side_lane(pos: int, *, w: int, h: int) -> tuple[str, int]:
    """
    Map perimeter index to (side, lane), clockwise:
      top:    x=0..w-1
      right:  y=0..h-1
      bottom: x=w-1..0
      left:   y=h-1..0
    """
    L = perimeter_len(w, h)
    if not (0 <= pos < L):
        raise ValueError("pos out of range")

    if pos < w:
        return ("top", pos)
    pos -= w
    if pos < h:
        return ("right", pos)
    pos -= h
    if pos < w:
        return ("bottom", (w - 1) - pos)
    pos -= w
    # left
    return ("left", (h - 1) - pos)


def _row_col_extrema(slots: list[list[int | None]]) -> tuple[list[int | None], list[int | None], list[int | None], list[int | None]]:
    h = len(slots)
    w = len(slots[0]) if h else 0
    row_min: list[int | None] = [None for _ in range(h)]
    row_max: list[int | None] = [None for _ in range(h)]
    col_min: list[int | None] = [None for _ in range(w)]
    col_max: list[int | None] = [None for _ in range(w)]

    for y in range(h):
        for x in range(w):
            if slots[y][x] is None:
                continue
            mn = row_min[y]
            mx = row_max[y]
            row_min[y] = x if mn is None else min(mn, x)
            row_max[y] = x if mx is None else max(mx, x)

            mn = col_min[x]
            mx = col_max[x]
            col_min[x] = y if mn is None else min(mn, y)
            col_max[x] = y if mx is None else max(mx, y)

    return row_min, row_max, col_min, col_max


def _target_for_lane(
    side: str,
    lane: int,
    *,
    row_min: list[int | None],
    row_max: list[int | None],
    col_min: list[int | None],
    col_max: list[int | None],
) -> tuple[int, int] | None:
    if side == "left":
        x = row_min[lane]
        return None if x is None else (x, lane)
    if side == "right":
        x = row_max[lane]
        return None if x is None else (x, lane)
    if side == "top":
        y = col_min[lane]
        return None if y is None else (lane, y)
    if side == "bottom":
        y = col_max[lane]
        return None if y is None else (lane, y)
    raise ValueError(f"unknown side: {side}")


def connected_component(top: list[list[int | None]], x0: int, y0: int) -> list[tuple[int, int]]:
    h = len(top)
    w = len(top[0]) if h else 0
    if not (0 <= x0 < w and 0 <= y0 < h):
        return []
    c = top[y0][x0]
    if c is None:
        return []
    q: deque[tuple[int, int]] = deque([(x0, y0)])
    seen = {(x0, y0)}
    out: list[tuple[int, int]] = []
    while q:
        x, y = q.popleft()
        out.append((x, y))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and top[ny][nx] == c:
                seen.add((nx, ny))
                q.append((nx, ny))
    return out


def all_components(top: list[list[int | None]]) -> list[list[tuple[int, int]]]:
    h = len(top)
    w = len(top[0]) if h else 0
    seen = [[False for _ in range(w)] for _ in range(h)]
    comps: list[list[tuple[int, int]]] = []
    for y in range(h):
        for x in range(w):
            if seen[y][x] or top[y][x] is None:
                continue
            pts = connected_component(top, x, y)
            for xx, yy in pts:
                seen[yy][xx] = True
            comps.append(pts)
    # Deterministic order: largest first, then top-left of component.
    def key(pts: list[tuple[int, int]]) -> tuple[int, int, int]:
        miny = min(p[1] for p in pts)
        minx = min(p[0] for p in pts if p[1] == miny)
        return (-len(pts), miny, minx)

    comps.sort(key=key)
    return comps


def apply_tap(
    *,
    top: list[list[int | None]],
    slots: list[list[int | None]],
    shooters: list[Shooter],
    tap_xy: tuple[int, int],
    cfg: GameConfig,
) -> tuple[list[list[int | None]], list[list[int | None]], list[Shooter]] | None:
    """
    Tap merges a connected component of the top grid into a shooter.
    Returns new (top, slots, shooters) or None if tap invalid/illegal (e.g. conveyor full).

    Assumption: tapped top cells are removed immediately; shooter color is the component color.
    """
    if len(shooters) >= cfg.conveyor_capacity:
        return None

    x0, y0 = tap_xy
    pts = connected_component(top, x0, y0)
    if not pts:
        return None
    color = top[y0][x0]
    if color is None:
        return None
    ammo = len(pts)

    new_top = [row[:] for row in top]
    for x, y in pts:
        new_top[y][x] = None

    new_slots = slots  # unchanged by tap directly
    new_shooters = list(shooters) + [Shooter(color=int(color), ammo=ammo, pos=cfg.entrance_pos)]
    return new_top, new_slots, new_shooters


def tick(
    *,
    top: list[list[int | None]],
    slots: list[list[int | None]],
    shooters: list[Shooter],
    w: int,
    h: int,
    cfg: GameConfig,
) -> tuple[list[list[int | None]], list[list[int | None]], list[Shooter], int]:
    """
    Advance by one deterministic tick. Returns (top, slots, shooters, shots_fired).

    Assumptions:
    - Shooters move one perimeter step clockwise per tick.
    - After movement, each shooter may fire at most once, determined by its side+lane.
    - A successful shot removes the target slot, and also removes the corresponding top cell if present.
    """
    L = perimeter_len(w, h)
    if L <= 0:
        return top, slots, shooters, 0

    new_top = [row[:] for row in top]
    new_slots = [row[:] for row in slots]

    moved: list[Shooter] = []
    if cfg.move_then_fire:
        for sh in shooters:
            moved.append(Shooter(color=sh.color, ammo=sh.ammo, pos=(sh.pos + 1) % L))
    else:
        moved = list(shooters)

    # Deterministic processing: sort by position then color then ammo.
    moved.sort(key=lambda s: (s.pos, s.color, s.ammo))

    row_min, row_max, col_min, col_max = _row_col_extrema(new_slots)

    shots = 0
    out: list[Shooter] = []
    for sh in moved:
        side, lane = pos_to_side_lane(sh.pos, w=w, h=h)
        tgt = _target_for_lane(side, lane, row_min=row_min, row_max=row_max, col_min=col_min, col_max=col_max)
        if tgt is None:
            out.append(sh)
            continue
        tx, ty = tgt
        c = new_slots[ty][tx]
        if c is None or int(c) != sh.color:
            out.append(sh)
            continue

        # Fire: remove slot and corresponding top cell, decrement ammo.
        new_slots[ty][tx] = None
        new_top[ty][tx] = None
        shots += 1

        # Update extrema since a shot can expose deeper cells in the same lane.
        row_min, row_max, col_min, col_max = _row_col_extrema(new_slots)

        na = sh.ammo - 1
        if na > 0:
            out.append(Shooter(color=sh.color, ammo=na, pos=sh.pos))

    if not cfg.move_then_fire:
        # Movement after firing
        out = [Shooter(color=sh.color, ammo=sh.ammo, pos=(sh.pos + 1) % L) for sh in out]

    return new_top, new_slots, out, shots


def is_win(slots: list[list[int | None]]) -> bool:
    return all(c is None for row in slots for c in row)


def any_shot_possible(*, slots: list[list[int | None]], shooters: list[Shooter], w: int, h: int) -> bool:
    """
    Conservative deadlock check: if no shooter color matches any currently-exposed slot on any lane,
    then no shots will ever fire (since nothing changes without shots).
    """
    if not shooters:
        return False
    row_min, row_max, col_min, col_max = _row_col_extrema(slots)

    # Precompute exposed slots per side as a set of colors.
    exposed_colors: set[int] = set()
    for y in range(h):
        x = row_min[y]
        if x is not None and slots[y][x] is not None:
            exposed_colors.add(int(slots[y][x]))
        x = row_max[y]
        if x is not None and slots[y][x] is not None:
            exposed_colors.add(int(slots[y][x]))
    for x in range(w):
        y = col_min[x]
        if y is not None and slots[y][x] is not None:
            exposed_colors.add(int(slots[y][x]))
        y = col_max[x]
        if y is not None and slots[y][x] is not None:
            exposed_colors.add(int(slots[y][x]))

    return any(sh.color in exposed_colors for sh in shooters)


def is_deadlock(*, slots: list[list[int | None]], shooters: list[Shooter], w: int, h: int, cfg: GameConfig) -> bool:
    return len(shooters) >= cfg.conveyor_capacity and not any_shot_possible(slots=slots, shooters=shooters, w=w, h=h)

