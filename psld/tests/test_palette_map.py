from psld.palette_map import (
    hex_to_rgb,
    map_rgb_to_palette_luma_bucket,
    map_rgb_to_palette_nearest,
    normalize_hex_palette,
)


def test_normalize_hex_palette() -> None:
    pal = normalize_hex_palette(["e63946", " #457B9D "])
    assert pal == ["#E63946", "#457B9D"]


def test_map_rgb_to_palette_nearest_tie_break() -> None:
    # Exactly equidistant between (0,0,0) and (0,0,2) for pixel (0,0,1) in 1D,
    # but in squared distance it's still a tie; should pick lowest index.
    palette = [(0, 0, 0), (0, 0, 2)]
    assert map_rgb_to_palette_nearest((0, 0, 1), palette) == 0


def test_map_rgb_to_palette_luma_bucket() -> None:
    palette_hex = ["#000000", "#FFFFFF", "#FF0000"]
    palette_rgb = [hex_to_rgb(h) for h in palette_hex]
    # Sort by luma: black, red, white (red luma ~54).
    palette_by_luma = [0, 2, 1]
    # Pixel range: 0..255
    min_l = 0.0
    max_l = 255.0
    assert (
        map_rgb_to_palette_luma_bucket(
            (0, 0, 0),
            palette_rgb=palette_rgb,
            palette_by_luma=palette_by_luma,
            min_l=min_l,
            max_l=max_l,
        )
        == 0
    )
    assert (
        map_rgb_to_palette_luma_bucket(
            (255, 255, 255),
            palette_rgb=palette_rgb,
            palette_by_luma=palette_by_luma,
            min_l=min_l,
            max_l=max_l,
        )
        == 1
    )

