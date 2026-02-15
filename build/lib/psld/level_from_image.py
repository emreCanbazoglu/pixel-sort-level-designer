from __future__ import annotations

from .backward_slots import generate_backward_place_order, verify_forward_remove_order
from .image_to_grid import image_to_grid
from .models import Grid, Level


def level_from_image(
    path: str,
    *,
    w: int,
    h: int,
    colors: int = 5,
    alpha_threshold: int = 16,
    min_component_size: int = 2,
    background_hex: str = "#000000",
    fill_background: bool = False,
) -> Level:
    palette, cells = image_to_grid(
        path,
        w=w,
        h=h,
        colors=colors,
        alpha_threshold=alpha_threshold,
        min_component_size=min_component_size,
        background_hex=background_hex,
        fill_background=fill_background,
    )
    top = Grid(w=w, h=h, cells=cells)
    slots = top

    mask = top.mask()
    backward = generate_backward_place_order(mask)
    forward = list(reversed(backward))
    verify_forward_remove_order(mask, forward)

    return Level(
        version=1,
        w=w,
        h=h,
        palette=palette,
        top=top,
        slots=slots,
        backward_place_order=backward,
        forward_remove_order=forward,
        meta={
            "source": {"type": "image", "path": path},
            "alpha_threshold": alpha_threshold,
            "min_component_size": min_component_size,
            "background_hex": background_hex,
            "fill_background": fill_background,
        },
    )
