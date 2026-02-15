from psld.slots_from_top import derive_slots_from_top


def test_slots_rotate_preserves_histogram_and_changes_some_cells() -> None:
    top = [
        [0, 0, 1],
        [1, None, 2],
    ]
    res = derive_slots_from_top(top, mode="rotate", rotate_shift=None)
    assert res.occupied_cells == 5
    # Histogram preserved
    top_vals = sorted([c for row in top for c in row if c is not None])
    slot_vals = sorted([c for row in res.cells for c in row if c is not None])
    assert top_vals == slot_vals
    # Prefer not to keep everything the same (may not be 0 for pathological patterns, but here it should differ)
    same = 0
    for y in range(len(top)):
        for x in range(len(top[0])):
            if top[y][x] is not None and top[y][x] == res.cells[y][x]:
                same += 1
    assert same < res.occupied_cells


def test_slots_derangement_never_matches() -> None:
    top = [
        [0, 0, 1, 1],
        [2, 2, 3, 3],
    ]
    res = derive_slots_from_top(top, mode="derangement", rotate_shift=None)
    for y in range(len(top)):
        for x in range(len(top[0])):
            if top[y][x] is None:
                assert res.cells[y][x] is None
            else:
                assert res.cells[y][x] != top[y][x]


def test_slots_derangement_impossible_dominant_color() -> None:
    # 7 of 8 occupied are color 0 -> impossible to avoid matches while preserving histogram.
    top = [
        [0, 0, 0, 0],
        [0, 0, 0, 1],
    ]
    try:
        derive_slots_from_top(top, mode="derangement", rotate_shift=None)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "dominant color" in str(e) or "Cannot derive slots" in str(e)
