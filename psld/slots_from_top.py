from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SlotsDeriveResult:
    cells: list[list[int | None]]
    mode: str
    shift: int
    same_cell_count: int
    occupied_cells: int


class _Dinic:
    def __init__(self, n: int) -> None:
        self.n = n
        self.adj: list[list[int]] = [[] for _ in range(n)]
        self.to: list[int] = []
        self.cap: list[int] = []
        self.nxt: list[int] = []

    def add_edge(self, u: int, v: int, c: int) -> None:
        # forward
        self.adj[u].append(len(self.to))
        self.to.append(v)
        self.cap.append(c)
        self.nxt.append(len(self.adj[v]))
        # backward
        self.adj[v].append(len(self.to))
        self.to.append(u)
        self.cap.append(0)
        self.nxt.append(len(self.adj[u]) - 1)

    def max_flow(self, s: int, t: int) -> int:
        flow = 0
        INF = 10**18
        while True:
            level = [-1] * self.n
            q: list[int] = [s]
            level[s] = 0
            for u in q:
                for ei in self.adj[u]:
                    if self.cap[ei] > 0 and level[self.to[ei]] < 0:
                        level[self.to[ei]] = level[u] + 1
                        q.append(self.to[ei])
            if level[t] < 0:
                break

            it = [0] * self.n

            def dfs(u: int, f: int) -> int:
                if u == t:
                    return f
                for i in range(it[u], len(self.adj[u])):
                    it[u] = i
                    ei = self.adj[u][i]
                    v = self.to[ei]
                    if self.cap[ei] <= 0 or level[v] != level[u] + 1:
                        continue
                    pushed = dfs(v, min(f, self.cap[ei]))
                    if pushed:
                        self.cap[ei] -= pushed
                        self.cap[ei ^ 1] += pushed
                        return pushed
                return 0

            while True:
                pushed = dfs(s, INF)
                if not pushed:
                    break
                flow += pushed
        return flow


def _derive_slots_derangement(top_cells: list[list[int | None]]) -> SlotsDeriveResult:
    h = len(top_cells)
    w = len(top_cells[0]) if h else 0
    if h == 0 or w == 0:
        return SlotsDeriveResult(cells=[], mode="derangement", shift=0, same_cell_count=0, occupied_cells=0)
    if any(len(r) != w for r in top_cells):
        raise ValueError("top_cells must be rectangular")

    pos_by_color: dict[int, list[tuple[int, int]]] = {}
    for y in range(h):
        for x in range(w):
            c = top_cells[y][x]
            if c is None:
                continue
            pos_by_color.setdefault(int(c), []).append((x, y))

    colors = sorted(pos_by_color)
    n = sum(len(pos_by_color[c]) for c in colors)
    if n == 0:
        return SlotsDeriveResult(
            cells=[[None for _ in range(w)] for _ in range(h)],
            mode="derangement",
            shift=0,
            same_cell_count=0,
            occupied_cells=0,
        )
    if len(colors) == 1:
        raise ValueError("Cannot derive slots with per-cell mismatch using only 1 color")

    counts = {c: len(pos_by_color[c]) for c in colors}
    maxc = max(counts.values())
    if maxc * 2 > n:
        raise ValueError(
            f"Cannot derive slots with per-cell mismatch: dominant color has {maxc}/{n} occupied cells (>50%)"
        )

    # Build flow: groups (forbidden colors) -> assigned colors, with x[f,f]=0.
    # Supply and demand are the same histogram (counts).
    K = len(colors)
    src = 0
    grp0 = 1
    col0 = grp0 + K
    sink = col0 + K
    g = _Dinic(sink + 1)

    idx = {c: i for i, c in enumerate(colors)}
    for c in colors:
        i = idx[c]
        g.add_edge(src, grp0 + i, counts[c])
        g.add_edge(col0 + i, sink, counts[c])

    INF = 10**9
    for f in colors:
        fi = idx[f]
        for a in colors:
            ai = idx[a]
            if a == f:
                continue
            g.add_edge(grp0 + fi, col0 + ai, INF)

    flowed = g.max_flow(src, sink)
    if flowed != n:
        raise ValueError("Could not find a per-cell mismatch assignment (flow infeasible)")

    # Extract x[f,a] from residual graph: look at reverse edges capacity (flow sent).
    # We know the order we added edges, so scan adjacency from group nodes.
    alloc: dict[tuple[int, int], int] = {}
    for f in colors:
        fi = idx[f]
        u = grp0 + fi
        for ei in g.adj[u]:
            v = g.to[ei]
            if not (col0 <= v < col0 + K):
                continue
            ai = v - col0
            a = colors[ai]
            if a == f:
                continue
            # Flow is stored in the reverse edge cap (since we increase cap on back edge).
            rev_ei = ei ^ 1
            sent = g.cap[rev_ei]
            if sent > 0:
                alloc[(f, a)] = int(sent)

    out = [[None for _ in range(w)] for _ in range(h)]
    # Fill each forbidden-color group positions in scan order, using assigned colors in increasing order.
    for f in colors:
        pts = pos_by_color[f]
        i = 0
        for a in colors:
            if a == f:
                continue
            k = alloc.get((f, a), 0)
            for _ in range(k):
                x, y = pts[i]
                out[y][x] = a
                i += 1
        if i != len(pts):
            raise RuntimeError("Internal error: allocation did not fill group")

    # Verify no occupied cell matches.
    same = 0
    for y in range(h):
        for x in range(w):
            tc = top_cells[y][x]
            if tc is None:
                continue
            if out[y][x] == int(tc):
                same += 1
    if same != 0:
        raise RuntimeError("Internal error: derangement produced same-cell matches")

    return SlotsDeriveResult(cells=out, mode="derangement", shift=0, same_cell_count=0, occupied_cells=n)


def derive_slots_from_top(
    top_cells: list[list[int | None]],
    *,
    mode: str = "derangement",  # "same" | "rotate" | "derangement"
    rotate_shift: int | None = None,
) -> SlotsDeriveResult:
    """
    Derive bottom slots colors from the top grid deterministically.

    Goals:
    - Keep the same occupied mask (None stays None).
    - Keep the same per-color histogram (so total ammo by color can match slot demand by color).
    - Make per-cell colors differ from top as much as possible.

    Current implementation uses a rotation over the occupied cells in a deterministic scan order.
    """
    h = len(top_cells)
    w = len(top_cells[0]) if h else 0
    if h == 0 or w == 0:
        return SlotsDeriveResult(cells=[], mode=mode, shift=0, same_cell_count=0, occupied_cells=0)
    if any(len(r) != w for r in top_cells):
        raise ValueError("top_cells must be rectangular")

    if mode == "same":
        cells = [row[:] for row in top_cells]
        occ = sum(1 for row in top_cells for c in row if c is not None)
        return SlotsDeriveResult(cells=cells, mode=mode, shift=0, same_cell_count=occ, occupied_cells=occ)

    if mode == "derangement":
        return _derive_slots_derangement(top_cells)

    if mode != "rotate":
        raise ValueError(f"Unknown slots derive mode: {mode}")

    # Scan order: y-major, x-major.
    pos: list[tuple[int, int]] = []
    vals: list[int] = []
    for y in range(h):
        for x in range(w):
            c = top_cells[y][x]
            if c is None:
                continue
            pos.append((x, y))
            vals.append(int(c))

    n = len(vals)
    if n == 0:
        cells = [[None for _ in range(w)] for _ in range(h)]
        return SlotsDeriveResult(cells=cells, mode=mode, shift=0, same_cell_count=0, occupied_cells=0)
    if n == 1:
        # Cannot differ.
        cells = [[None for _ in range(w)] for _ in range(h)]
        x, y = pos[0]
        cells[y][x] = vals[0]
        return SlotsDeriveResult(cells=cells, mode=mode, shift=0, same_cell_count=1, occupied_cells=1)

    def same_count_for_shift(k: int) -> int:
        return sum(1 for i in range(n) if vals[i] == vals[(i + k) % n])

    if rotate_shift is None:
        # Pick a shift that minimizes same-cell matches; deterministic tie-break = smallest shift.
        best_k = 1
        best_same = same_count_for_shift(1)
        for k in range(2, n):
            s = same_count_for_shift(k)
            if s < best_same:
                best_same = s
                best_k = k
                if best_same == 0:
                    break
        k = best_k
        same_cnt = best_same
    else:
        k = int(rotate_shift) % n
        if k == 0:
            k = 1
        same_cnt = same_count_for_shift(k)

    out = [[None for _ in range(w)] for _ in range(h)]
    for i, (x, y) in enumerate(pos):
        out[y][x] = vals[(i + k) % n]

    return SlotsDeriveResult(cells=out, mode=mode, shift=k, same_cell_count=same_cnt, occupied_cells=n)
