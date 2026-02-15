from __future__ import annotations

from .backward_slots import generate_backward_place_order, verify_forward_remove_order
from .coloring import colorize_mask, colorize_mask_filled
from .models import Level, Grid
from .slots_from_top import derive_slots_from_top
from .word_mask import render_word_template_mask


def level_from_word(
    word: str,
    *,
    w: int,
    h: int,
    palette_size: int = 4,
    color_mode: str = "vertical_stripes",
    padding: int = 1,
    fill_background: bool = False,
    background_index: int = 0,
) -> Level:
    mask = render_word_template_mask(word, w=w, h=h, padding=padding)

    if fill_background:
        palette, top = colorize_mask_filled(
            mask,
            palette_size=palette_size,
            mode=color_mode,
            background_index=background_index,
        )
        slots_mask = [[True for _ in range(w)] for _ in range(h)]
    else:
        palette, top = colorize_mask(mask, palette_size=palette_size, mode=color_mode)
        slots_mask = mask
    slots_derived = derive_slots_from_top(top.cells, mode="derangement", rotate_shift=None)
    slots = Grid(w=top.w, h=top.h, cells=slots_derived.cells)

    backward = generate_backward_place_order(slots_mask)
    forward = list(reversed(backward))
    verify_forward_remove_order(slots_mask, forward)

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
            "source": {"type": "word", "word": word},
            "color_mode": color_mode,
            "padding": padding,
            "fill_background": fill_background,
            "background_index": background_index if fill_background else None,
            "slots_mode": slots_derived.mode,
            "slots_rotate_shift": slots_derived.shift,
            "slots_same_cell_count": slots_derived.same_cell_count,
            "slots_occupied_cells": slots_derived.occupied_cells,
        },
    )
