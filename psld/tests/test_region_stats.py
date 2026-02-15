from psld.region_stats import analyze_grid_regions, validate_grid_regions


def test_analyze_grid_regions_basic() -> None:
    # Two colors, each forms one region. Includes empty.
    cells = [
        [0, 0, None],
        [0, 1, 1],
        [None, 1, 1],
    ]
    s = analyze_grid_regions(cells)
    assert s.occupied_cells == 7
    assert s.empty_cells == 2
    assert s.total_regions == 2
    assert abs(s.fragmentation - (2 / 7)) < 1e-9
    assert len(s.colors) == 2
    assert s.colors[0].color_index == 0
    assert s.colors[0].regions == 1
    assert s.colors[0].largest == 3
    assert s.colors[1].color_index == 1
    assert s.colors[1].regions == 1
    assert s.colors[1].largest == 4


def test_validate_grid_regions_thresholds() -> None:
    cells = [
        [0, None, 0],
        [None, 0, None],
        [0, None, 0],
    ]
    # 5 isolated 1-cell regions for color 0.
    res = validate_grid_regions(cells, min_largest_region=2)
    assert res.ok is False
    assert any("largest_region" in r for r in res.reasons)


def test_validate_grid_regions_max_largest_and_share() -> None:
    cells = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, None, None],
        [0, 0, None, None],
    ]
    # color 0 has a 12-cell region and 100% share of occupied.
    res = validate_grid_regions(cells, max_largest_region=10, max_color_share=0.9)
    assert res.ok is False
    assert any("max_largest_region" in r for r in res.reasons) or any("> max_largest_region" in r for r in res.reasons)
    assert any("max_color_share" in r for r in res.reasons) or any("> max_color_share" in r for r in res.reasons)
