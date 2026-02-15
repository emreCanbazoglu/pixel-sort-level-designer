from __future__ import annotations

from dataclasses import dataclass
import os

from .level_from_text import level_from_text
from .level_from_word import level_from_word
from .backward_slots import generate_backward_place_order, verify_forward_remove_order
from .coloring import colorize_mask
from .llm_openai import OpenAIConfig, generate_mask_candidates_via_openai
from .mask_ops import mask_from_strings, remove_small_foreground_components
from .models import Level


@dataclass(frozen=True, slots=True)
class AgentRequest:
    prompt: str
    w: int = 24
    h: int = 24
    colors: int = 5
    color_mode: str = "vertical_stripes"
    padding: int = 1
    provider: str = "offline"  # "offline" or "openai"
    model: str = "gpt-4o-mini"
    cache_dir: str | None = ".psld_cache"
    min_fg_component: int = 2
    candidates: int = 6


def _prompt_keywords(prompt: str) -> set[str]:
    # Very small, deterministic normalization.
    return {t for t in "".join(ch if ch.isalnum() else " " for ch in prompt.lower()).split() if t}


def generate_level_from_prompt(req: AgentRequest):
    """
    "Agent" entry point (offline).

    Today, this is a deterministic router:
      - If the prompt matches a known template word (e.g. CAT), use that silhouette.
      - Otherwise, fall back to rendering literal text.

    This keeps the system functional without network/model dependencies.

    Next step (when you pick a provider): replace the fallback with prompt->image or prompt->mask synthesis,
    then gate candidates with the solver.
    """
    if req.provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set (required for provider=openai)")

        cfg = OpenAIConfig(api_key=api_key, model=req.model)
        obj = generate_mask_candidates_via_openai(
            prompt=req.prompt,
            w=req.w,
            h=req.h,
            cfg=cfg,
            cache_dir=req.cache_dir,
            candidates=req.candidates,
        )

        kw = _prompt_keywords(req.prompt)

        def score(mask: list[list[bool]]) -> float:
            # Generic: prefer a large connected dominant shape and some margin.
            # Also reward horizontal symmetry, which helps many icons (and cats).
            h = len(mask)
            w = len(mask[0]) if h else 0
            fg = [(x, y) for y in range(h) for x in range(w) if mask[y][x]]
            if not fg:
                return -1e9
            xs = [p[0] for p in fg]
            ys = [p[1] for p in fg]
            minx, maxx = min(xs), max(xs)
            miny, maxy = min(ys), max(ys)
            area = len(fg)
            bbox_area = (maxx - minx + 1) * (maxy - miny + 1)
            compact = area / max(1, bbox_area)

            # Symmetry about vertical center.
            sym = 0
            total = 0
            for y in range(h):
                for x in range(w // 2):
                    total += 1
                    if mask[y][x] == mask[y][w - 1 - x]:
                        sym += 1
            sym_score = sym / max(1, total)

            # Margin: prefer not touching bounds too much.
            touch = 0
            for x in range(w):
                if mask[0][x] or mask[h - 1][x]:
                    touch += 1
            for y in range(h):
                if mask[y][0] or mask[y][w - 1]:
                    touch += 1
            touch_pen = touch / (2 * w + 2 * h)

            s = 3.0 * compact + 2.0 * sym_score - 2.0 * touch_pen

            if "cat" in kw or "kitten" in kw:
                # Cat heuristic: look for two ear-ish bumps in the top quarter.
                top_h = max(2, h // 4)
                # Find first row with any fg in top quarter.
                ear_row = None
                for y in range(top_h):
                    if any(mask[y][x] for x in range(w)):
                        ear_row = y
                        break
                if ear_row is not None:
                    segs = 0
                    in_seg = False
                    for x in range(w):
                        if mask[ear_row][x]:
                            if not in_seg:
                                segs += 1
                                in_seg = True
                        else:
                            in_seg = False
                    # Prefer 2-3 segments (ears + maybe head connection).
                    if segs == 2:
                        s += 2.0
                    elif segs == 3:
                        s += 1.0
                    else:
                        s -= 1.0
            return s

        best = None
        best_s = -1e18
        best_notes = ""
        best_idx = -1
        for i, cand in enumerate(obj["candidates"]):
            m = mask_from_strings(cand["mask"])
            m = remove_small_foreground_components(m, min_size=req.min_fg_component)
            sc = score(m)
            if sc > best_s:
                best_s = sc
                best = m
                best_notes = str(cand.get("notes", ""))
                best_idx = i

        if best is None:
            raise RuntimeError("No valid mask candidates returned")
        mask = best

        palette, top = colorize_mask(mask, palette_size=req.colors, mode=req.color_mode)
        slots = top

        backward = generate_backward_place_order(mask)
        forward = list(reversed(backward))
        verify_forward_remove_order(mask, forward)

        return Level(
            version=1,
            w=req.w,
            h=req.h,
            palette=palette,
            top=top,
            slots=slots,
            backward_place_order=backward,
            forward_remove_order=forward,
            meta={
                "source": {"type": "prompt", "provider": "openai", "prompt": req.prompt, "model": req.model},
                "min_fg_component": req.min_fg_component,
                "candidate_count": req.candidates,
                "picked_candidate_index": best_idx,
                "picked_candidate_notes": best_notes,
                "picked_candidate_score": best_s,
            },
        )

    kw = _prompt_keywords(req.prompt)

    # Prefer a silhouette template when available.
    if "cat" in kw:
        return level_from_word(
            "CAT",
            w=req.w,
            h=req.h,
            palette_size=req.colors,
            color_mode=req.color_mode,
            padding=req.padding,
            fill_background=False,
        )

    # Fallback: literal text.
    return level_from_text(
        req.prompt,
        w=req.w,
        h=req.h,
        palette_size=req.colors,
        color_mode=req.color_mode,
        padding=req.padding,
        fill_background=False,
    )
