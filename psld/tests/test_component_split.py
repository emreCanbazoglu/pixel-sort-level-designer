from psld.component_split import split_large_components
from psld.region_stats import analyze_grid_regions


def test_split_large_component_sectors_reduces_largest() -> None:
    # Single large component of color 0.
    cells = [[0 for _ in range(10)] for _ in range(10)]  # 100 cells
    split_large_components(cells, palette_size=3, max_component_size=25, mode="sectors")
    s = analyze_grid_regions(cells)
    # Should now contain multiple colors/regions; largest region should be smaller than original.
    assert s.total_regions >= 2
    largest_any = max(cs.largest for cs in s.colors)
    assert largest_any < 100

