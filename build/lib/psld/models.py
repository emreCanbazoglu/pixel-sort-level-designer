from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


ColorHex = str  # "#RRGGBB"


@dataclass(frozen=True, slots=True)
class Pos:
    x: int
    y: int


GridCell = int | None  # palette index, or None for empty


@dataclass(frozen=True, slots=True)
class Grid:
    w: int
    h: int
    cells: list[list[GridCell]]  # rows, y-major

    def __post_init__(self) -> None:
        if self.h <= 0 or self.w <= 0:
            raise ValueError("Grid dimensions must be positive")
        if len(self.cells) != self.h:
            raise ValueError(f"cells height mismatch: expected {self.h}, got {len(self.cells)}")
        for row in self.cells:
            if len(row) != self.w:
                raise ValueError(f"cells width mismatch: expected {self.w}, got {len(row)}")

    def mask(self) -> list[list[bool]]:
        return [[c is not None for c in row] for row in self.cells]


@dataclass(frozen=True, slots=True)
class Level:
    version: int
    w: int
    h: int
    palette: list[ColorHex]
    top: Grid
    slots: Grid
    backward_place_order: list[Pos]  # inner -> outer (reverse-time placement)
    forward_remove_order: list[Pos]  # outer -> inner (play-time clearing)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        # Keep it explicit for stable serialization.
        def grid_to_list(g: Grid) -> list[list[int | None]]:
            return g.cells

        def pos_list(ps: list[Pos]) -> list[dict[str, int]]:
            return [{"x": p.x, "y": p.y} for p in ps]

        return {
            "version": self.version,
            "w": self.w,
            "h": self.h,
            "palette": list(self.palette),
            "top": grid_to_list(self.top),
            "slots": grid_to_list(self.slots),
            "backward_place_order": pos_list(self.backward_place_order),
            "forward_remove_order": pos_list(self.forward_remove_order),
            "meta": dict(self.meta),
        }


SourceType = Literal["text", "image"]

