from __future__ import annotations

import json
from collections import Counter
from typing import Literal


PreviewView = Literal["mask", "idx"]


def _idx_char(i: int) -> str:
    # 0-9 then A-Z
    if 0 <= i <= 9:
        return str(i)
    j = i - 10
    if 0 <= j < 26:
        return chr(ord("A") + j)
    return "?"


def preview_level_json(
    path: str,
    *,
    view: PreviewView = "mask",
) -> str:
    d = json.load(open(path, "r", encoding="utf-8"))
    slots = d["slots"]
    palette = d.get("palette", [])

    h = len(slots)
    w = len(slots[0]) if h else 0

    lines: list[str] = []
    lines.append(f"{path} ({w}x{h})")

    if view == "mask":
        for row in slots:
            lines.append("".join("#" if c is not None else "." for c in row))
    elif view == "idx":
        for row in slots:
            lines.append("".join("." if c is None else _idx_char(int(c)) for c in row))
    else:
        raise ValueError(f"unknown view: {view}")

    # Palette legend + counts
    cnt = Counter(c for row in slots for c in row if c is not None)
    if palette:
        lines.append("")
        lines.append("palette:")
        for i, hx in enumerate(palette):
            n = cnt.get(i, 0)
            lines.append(f"  {i:>2} {_idx_char(i)} {hx}  count={n}")
    else:
        lines.append("")
        lines.append("palette: <missing>")

    lines.append("")
    lines.append(f"empty(null) cells: {sum(1 for row in slots for c in row if c is None)}")
    return "\n".join(lines) + "\n"

