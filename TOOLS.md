# Tools (Python)

This repo currently ships a small Python toolkit to turn **words** (and optionally **images**) into JSON grid levels.

## Install

Text-only (no image support):

```bash
python3 -m pip install -e .
```

With image support (requires Pillow):

```bash
python3 -m pip install -e ".[image]"
```

## Generate From Text

```bash
python3 -m psld from-text CAT --w 16 --h 16 --colors 4 --color-mode vertical_stripes --out level.json
```

This renders literal letters. By default it keeps empty cells as `null` (so the "background" cannot be tapped into a giant shooter).
If you want a fully-filled grid anyway, add `--fill-background`.
If you want `CAT` to mean an actual cat silhouette, use `from-word`.

## Generate From Word Template (Silhouette)

```bash
python3 -m psld from-word CAT --w 16 --h 16 --colors 4 --color-mode vertical_stripes --out cat.json
```

## Generate From Image (PNG recommended)

Requires `pip install -e ".[image]"`.

```bash
python3 -m psld from-image path/to/icon.png --w 24 --h 24 --colors 5 --out level.json
```

Also write a pixelized preview PNG (recommended workflow):

```bash
python3 -m psld from-image path/to/icon.png --w 48 --h 48 --colors 5 --out level.json --out-png preview.png --png-scale 12
```

Notes:
- Transparent pixels stay empty (`null`) by default. If you want to fill them, add `--fill-background --background '#000000'`.
- Non-transparent pixels are quantized to `--colors` (median-cut).
- Very small color components can be merged into neighbors via `--min-component-size`.

## Export A PNG Preview

Requires `pip install -e ".[image]"`.

```bash
python3 -m psld export-png level.json --out level.png
python3 -m psld export-png level.json --layer top --out top.png
```

## Generate From Prompt (Offline "Agent" Router)

This is an offline placeholder "agent" that routes prompts to known silhouettes when possible, otherwise renders text.

```bash
python3 -m psld from-prompt "cat icon" --w 24 --h 24 --colors 5 --out cat.json
```

### Online LLM (OpenAI)

Set `OPENAI_API_KEY`, then:

```bash
python3 -m psld from-prompt "sleeping cat icon" --provider openai --model gpt-4o-mini --w 32 --h 32 --colors 5 --out cat.json
```
