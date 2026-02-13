from __future__ import annotations

import argparse
import json
import sys

from .level_from_image import level_from_image
from .agent import AgentRequest, generate_level_from_prompt
from .level_from_text import level_from_text
from .level_from_word import level_from_word
from .preview import preview_level_json
from .render_png import level_json_to_png


def _cmd_from_text(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="psld from-text")
    ap.add_argument("text", type=str)
    ap.add_argument("--w", type=int, default=16)
    ap.add_argument("--h", type=int, default=16)
    ap.add_argument("--colors", type=int, default=4)
    ap.add_argument(
        "--color-mode",
        type=str,
        default="vertical_stripes",
        choices=["solid", "vertical_stripes", "quadrants"],
    )
    ap.add_argument("--padding", type=int, default=1)
    ap.add_argument("--fill-background", action="store_true", help="Fill empty cells with a background color index")
    ap.add_argument("--background-index", type=int, default=0, help="Palette index used when --fill-background")
    ap.add_argument("--out", type=str, default="-", help="Output path or '-' for stdout")
    ns = ap.parse_args(argv)

    lvl = level_from_text(
        ns.text,
        w=ns.w,
        h=ns.h,
        palette_size=ns.colors,
        color_mode=ns.color_mode,
        padding=ns.padding,
        fill_background=ns.fill_background,
        background_index=ns.background_index,
    )
    payload = lvl.to_json_dict()

    data = json.dumps(payload, indent=2, sort_keys=True)
    if ns.out == "-":
        sys.stdout.write(data + "\n")
    else:
        with open(ns.out, "w", encoding="utf-8") as f:
            f.write(data + "\n")
    return 0


def _cmd_from_word(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="psld from-word")
    ap.add_argument("word", type=str, help="Template name, e.g. CAT")
    ap.add_argument("--w", type=int, default=16)
    ap.add_argument("--h", type=int, default=16)
    ap.add_argument("--colors", type=int, default=4)
    ap.add_argument(
        "--color-mode",
        type=str,
        default="vertical_stripes",
        choices=["solid", "vertical_stripes", "quadrants"],
    )
    ap.add_argument("--padding", type=int, default=1)
    ap.add_argument("--fill-background", action="store_true", help="Fill empty cells with a background color index")
    ap.add_argument("--background-index", type=int, default=0, help="Palette index used when --fill-background")
    ap.add_argument("--out", type=str, default="-", help="Output path or '-' for stdout")
    ns = ap.parse_args(argv)

    lvl = level_from_word(
        ns.word,
        w=ns.w,
        h=ns.h,
        palette_size=ns.colors,
        color_mode=ns.color_mode,
        padding=ns.padding,
        fill_background=ns.fill_background,
        background_index=ns.background_index,
    )
    payload = lvl.to_json_dict()

    data = json.dumps(payload, indent=2, sort_keys=True)
    if ns.out == "-":
        sys.stdout.write(data + "\n")
    else:
        with open(ns.out, "w", encoding="utf-8") as f:
            f.write(data + "\n")
    return 0


def _cmd_from_image(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="psld from-image")
    ap.add_argument("path", type=str)
    ap.add_argument("--w", type=int, default=16)
    ap.add_argument("--h", type=int, default=16)
    ap.add_argument("--colors", type=int, default=5)
    ap.add_argument("--alpha-threshold", type=int, default=16)
    ap.add_argument("--min-component-size", type=int, default=2)
    ap.add_argument("--fill-background", action="store_true", help="Fill transparent pixels with --background")
    ap.add_argument("--background", type=str, default="#000000", help="Background color when --fill-background")
    ap.add_argument("--out-png", type=str, default=None, help="Optional PNG preview path (requires Pillow)")
    ap.add_argument("--png-scale", type=int, default=16, help="Cell size for --out-png")
    ap.add_argument("--png-layer", type=str, default="slots", choices=["slots", "top"])
    ap.add_argument("--no-png-grid", action="store_true", help="Disable grid lines in --out-png")
    ap.add_argument("--out", type=str, default="-", help="Output path or '-' for stdout")
    ns = ap.parse_args(argv)

    lvl = level_from_image(
        ns.path,
        w=ns.w,
        h=ns.h,
        colors=ns.colors,
        alpha_threshold=ns.alpha_threshold,
        min_component_size=ns.min_component_size,
        background_hex=ns.background,
        fill_background=ns.fill_background,
    )
    payload = lvl.to_json_dict()

    data = json.dumps(payload, indent=2, sort_keys=True)
    if ns.out == "-":
        if ns.out_png:
            raise SystemExit("--out-png requires --out to be a file path (not stdout)")
        sys.stdout.write(data + "\n")
    else:
        with open(ns.out, "w", encoding="utf-8") as f:
            f.write(data + "\n")
        if ns.out_png:
            level_json_to_png(
                ns.out,
                out_path=ns.out_png,
                layer=ns.png_layer,
                scale=ns.png_scale,
                draw_grid=not ns.no_png_grid,
            )
    return 0


def _cmd_from_prompt(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="psld from-prompt")
    ap.add_argument("prompt", type=str)
    ap.add_argument("--w", type=int, default=24)
    ap.add_argument("--h", type=int, default=24)
    ap.add_argument("--colors", type=int, default=5)
    ap.add_argument("--provider", type=str, default="offline", choices=["offline", "openai"])
    ap.add_argument("--model", type=str, default="gpt-4o-mini", help="When --provider openai")
    ap.add_argument("--cache-dir", type=str, default=".psld_cache", help="When --provider openai")
    ap.add_argument("--min-fg-component", type=int, default=2, help="Remove tiny foreground specks (<N)")
    ap.add_argument("--candidates", type=int, default=6, help="When --provider openai: generate N candidates and pick best")
    ap.add_argument(
        "--color-mode",
        type=str,
        default="vertical_stripes",
        choices=["solid", "vertical_stripes", "quadrants"],
    )
    ap.add_argument("--padding", type=int, default=1)
    ap.add_argument("--out", type=str, default="-", help="Output path or '-' for stdout")
    ns = ap.parse_args(argv)

    req = AgentRequest(
        prompt=ns.prompt,
        w=ns.w,
        h=ns.h,
        colors=ns.colors,
        color_mode=ns.color_mode,
        padding=ns.padding,
        provider=ns.provider,
        model=ns.model,
        cache_dir=ns.cache_dir if ns.cache_dir else None,
        min_fg_component=ns.min_fg_component,
        candidates=ns.candidates,
    )
    lvl = generate_level_from_prompt(req)
    payload = lvl.to_json_dict()

    data = json.dumps(payload, indent=2, sort_keys=True)
    if ns.out == "-":
        sys.stdout.write(data + "\n")
    else:
        with open(ns.out, "w", encoding="utf-8") as f:
            f.write(data + "\n")
    return 0


def _cmd_preview(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="psld preview")
    ap.add_argument("path", type=str, help="Path to a level .json")
    ap.add_argument("--view", type=str, default="mask", choices=["mask", "idx"])
    ns = ap.parse_args(argv)

    sys.stdout.write(preview_level_json(ns.path, view=ns.view))
    return 0


def _cmd_export_png(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="psld export-png")
    ap.add_argument("level_json", type=str)
    ap.add_argument("--layer", type=str, default="slots", choices=["slots", "top"])
    ap.add_argument("--scale", type=int, default=16)
    ap.add_argument("--no-grid", action="store_true")
    ap.add_argument("--out", type=str, required=True, help="Output .png path")
    ns = ap.parse_args(argv)

    level_json_to_png(
        ns.level_json,
        out_path=ns.out,
        layer=ns.layer,
        scale=ns.scale,
        draw_grid=not ns.no_grid,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("psld commands: from-text, from-word, from-image, from-prompt, preview, export-png")
        print("Example: psld from-text CAT --w 16 --h 16 --colors 4 --out level.json")
        print("Example: psld from-word CAT --w 16 --h 16 --colors 4 --out cat.json")
        print("Example: psld from-prompt 'cat icon' --w 24 --h 24 --colors 5 --out cat.json")
        print("Example: psld from-prompt 'cat icon' --provider openai --w 32 --h 32 --colors 5 --out cat.json")
        print("Example: psld export-png level.json --out level.png")
        return 0

    cmd = argv[0]
    sub_argv = argv[1:]
    if cmd == "from-text":
        return _cmd_from_text(sub_argv)
    if cmd == "from-word":
        return _cmd_from_word(sub_argv)
    if cmd == "from-image":
        return _cmd_from_image(sub_argv)
    if cmd == "from-prompt":
        return _cmd_from_prompt(sub_argv)
    if cmd == "preview":
        return _cmd_preview(sub_argv)
    if cmd == "export-png":
        return _cmd_export_png(sub_argv)

    print(f"Unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
