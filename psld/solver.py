from __future__ import annotations

from dataclasses import dataclass
from collections import deque

from .sim import GameConfig, Shooter, all_components, apply_tap, is_deadlock, is_win, tick


@dataclass(frozen=True, slots=True)
class SolveResult:
    solvable: bool
    steps: int | None
    expanded: int
    reason: str
    # Solution is a list of actions; ("tap", x, y) or ("wait", -1, -1)
    solution: list[tuple[str, int, int]] | None


def _flatten(grid: list[list[int | None]]) -> tuple[int, ...]:
    out: list[int] = []
    for row in grid:
        for c in row:
            out.append(-1 if c is None else int(c))
    return tuple(out)


def _unflatten(flat: tuple[int, ...], *, w: int, h: int) -> list[list[int | None]]:
    if len(flat) != w * h:
        raise ValueError("flat size mismatch")
    out: list[list[int | None]] = []
    i = 0
    for _y in range(h):
        row: list[int | None] = []
        for _x in range(w):
            v = flat[i]
            row.append(None if v < 0 else int(v))
            i += 1
        out.append(row)
    return out


def _canon_shooters(shooters: list[Shooter]) -> tuple[tuple[int, int, int], ...]:
    # Canonical multiset: (pos, color, ammo) sorted.
    return tuple(sorted(((s.pos, s.color, s.ammo) for s in shooters)))


def solve_level(
    *,
    top: list[list[int | None]],
    slots: list[list[int | None]],
    w: int,
    h: int,
    cfg: GameConfig,
    max_expanded: int = 50_000,
    max_steps: int = 80,
    allow_wait: bool = True,
) -> SolveResult:
    """
    BFS over discrete decision points:
    - action: tap a component (spawn shooter) OR wait 1 tick
    - environment: advance 1 tick after each action (movement + auto-fire)

    This is a baseline solver meant for small/medium grids; pruning/heuristics come later.
    """
    if is_win(slots):
        return SolveResult(solvable=True, steps=0, expanded=0, reason="already_clear", solution=[])

    start = (_flatten(top), _flatten(slots), _canon_shooters([]))

    q: deque[tuple[tuple[int, ...], tuple[int, ...], tuple[tuple[int, int, int], ...]]] = deque([start])
    prev: dict[tuple[tuple[int, ...], tuple[int, ...], tuple[tuple[int, int, int], ...]], tuple[
        tuple[tuple[int, ...], tuple[int, ...], tuple[tuple[int, int, int], ...]] | None,
        tuple[str, int, int] | None,
        int,
    ]] = {start: (None, None, 0)}

    expanded = 0

    def reconstruct(end_state):
        path: list[tuple[str, int, int]] = []
        cur = end_state
        while True:
            p, act, _d = prev[cur]
            if p is None:
                break
            if act is not None:
                path.append(act)
            cur = p
        path.reverse()
        return path

    while q:
        st = q.popleft()
        p_state, _p_act, depth = prev[st]
        if depth >= max_steps:
            continue

        top_g = _unflatten(st[0], w=w, h=h)
        slots_g = _unflatten(st[1], w=w, h=h)
        shooters = [Shooter(pos=p, color=c, ammo=a) for (p, c, a) in st[2]]

        # Losing state
        if is_deadlock(slots=slots_g, shooters=shooters, w=w, h=h, cfg=cfg):
            continue

        # Generate actions
        actions: list[tuple[str, int, int]] = []
        for comp in all_components(top_g):
            # Canonical representative: top-leftmost cell in the component.
            miny = min(p[1] for p in comp)
            minx = min(p[0] for p in comp if p[1] == miny)
            actions.append(("tap", minx, miny))
        if allow_wait:
            actions.append(("wait", -1, -1))

        # Deterministic action ordering: taps first, biggest components already earlier via all_components.
        for act, ax, ay in actions:
            if act == "tap":
                nxt = apply_tap(top=top_g, slots=slots_g, shooters=shooters, tap_xy=(ax, ay), cfg=cfg)
                if nxt is None:
                    continue
                ntop, nslots, nshooters = nxt
            else:
                ntop = top_g
                nslots = slots_g
                nshooters = shooters

            ntop2, nslots2, nshooters2, _shots = tick(
                top=ntop,
                slots=nslots,
                shooters=nshooters,
                w=w,
                h=h,
                cfg=cfg,
            )

            if is_win(nslots2):
                end_state = (_flatten(ntop2), _flatten(nslots2), _canon_shooters(nshooters2))
                if end_state not in prev:
                    prev[end_state] = (st, (act, ax, ay), depth + 1)
                return SolveResult(
                    solvable=True,
                    steps=depth + 1,
                    expanded=expanded,
                    reason="solved",
                    solution=reconstruct(end_state),
                )

            next_state = (_flatten(ntop2), _flatten(nslots2), _canon_shooters(nshooters2))
            if next_state in prev:
                continue

            prev[next_state] = (st, (act, ax, ay), depth + 1)
            q.append(next_state)

        expanded += 1
        if expanded >= max_expanded:
            break

    return SolveResult(
        solvable=False,
        steps=None,
        expanded=expanded,
        reason="search_exhausted" if expanded < max_expanded else "max_expanded",
        solution=None,
    )

