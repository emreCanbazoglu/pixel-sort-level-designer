from __future__ import annotations

from .backward_slots import generate_backward_place_order, verify_forward_remove_order
from .image_to_grid import image_to_grid
from .models import Grid, Level
from .slots_from_top import derive_slots_from_top
from .top_rebalance import rebalance_top_for_derangement


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
    recolor_mode: str = "source",  # "source" | "palette_map" | "silhouette"
    recolor_palette: list[str] | None = None,
    recolor_color_mode: str = "vertical_stripes",
    palette_map_mode: str = "nearest",  # "nearest" | "luma_buckets"
    split_max_component: int | None = None,
    split_mode: str = "sectors",
    split_cut_thickness: int = 1,
    mask_mode: str = "alpha",  # "alpha" or "auto"
    bg_tol: int = 32,
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
        recolor_mode=recolor_mode,
        recolor_palette=recolor_palette,
        recolor_color_mode=recolor_color_mode,
        palette_map_mode=palette_map_mode,
        split_max_component=split_max_component,
        split_mode=split_mode,
        split_cut_thickness=split_cut_thickness,
        mask_mode=mask_mode,
        bg_tol=bg_tol,
    )
    top_cells = cells
    reb = rebalance_top_for_derangement(top_cells, palette_size=len(palette), max_dominant_share=0.5)
    top_cells = reb.cells

    top = Grid(w=w, h=h, cells=top_cells)
    slots_derived = derive_slots_from_top(top.cells, mode="derangement", rotate_shift=None)
    slots = Grid(w=w, h=h, cells=slots_derived.cells)

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
            "recolor_mode": recolor_mode,
            "recolor_palette": recolor_palette,
            "recolor_color_mode": recolor_color_mode,
            "palette_map_mode": palette_map_mode,
            "split_max_component": split_max_component,
            "split_mode": split_mode,
            "split_cut_thickness": split_cut_thickness,
            "mask_mode": mask_mode,
            "bg_tol": bg_tol,
            "slots_mode": slots_derived.mode,
            "slots_rotate_shift": slots_derived.shift,
            "slots_same_cell_count": slots_derived.same_cell_count,
            "slots_occupied_cells": slots_derived.occupied_cells,
            "top_rebalanced": reb.ok and reb.iterations > 0,
            "top_rebalance_ok": reb.ok,
            "top_rebalance_iterations": reb.iterations,
            "top_rebalance_dominant_color": reb.dominant_color,
            "top_rebalance_dominant_share": reb.dominant_share,
        },
    )
