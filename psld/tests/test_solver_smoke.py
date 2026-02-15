from psld.sim import GameConfig
from psld.solver import solve_level


def test_solver_trivial_one_cell() -> None:
    # One occupied cell; tap creates shooter, tick fires once, clears.
    top = [[0]]
    slots = [[0]]
    res = solve_level(top=top, slots=slots, w=1, h=1, cfg=GameConfig(entrance_pos=0), max_expanded=1000, max_steps=10)
    assert res.solvable is True
    assert res.steps is not None and res.steps > 0


def test_solver_unsolvable_no_top_blocks() -> None:
    # Slot exists but no way to create a shooter.
    top = [[None]]
    slots = [[0]]
    res = solve_level(top=top, slots=slots, w=1, h=1, cfg=GameConfig(entrance_pos=0), max_expanded=200, max_steps=5)
    assert res.solvable is False
