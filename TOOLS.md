# Tools (Python)

This repo currently ships a small Python toolkit to turn **words** (and optionally **images**) into JSON grid levels.

## Install

This project requires **Python 3.11+**. Use a virtualenv. The helper `./scripts/py` will prefer:
- an active venv (`$VIRTUAL_ENV`)
- repo-local `.venv/`
- otherwise Homebrew Python (`/opt/homebrew/bin/python3`)

Text-only (no image support):

```bash
./scripts/py -m pip install -e .
```

With image support (requires Pillow):

```bash
./scripts/py -m pip install -e ".[image]"
```

## Generate From Text

```bash
./scripts/py -m psld from-text CAT --w 16 --h 16 --colors 4 --color-mode vertical_stripes --out level.json
```

This renders literal letters. By default it keeps empty cells as `null` (so the "background" cannot be tapped into a giant shooter).
If you want a fully-filled grid anyway, add `--fill-background`.
If you want `CAT` to mean an actual cat silhouette, use `from-word`.

## Generate From Word Template (Silhouette)

```bash
./scripts/py -m psld from-word CAT --w 16 --h 16 --colors 4 --color-mode vertical_stripes --out cat.json
```

## Generate From Image (PNG recommended)

Requires `pip install -e ".[image]"`.

```bash
./scripts/py -m psld from-image path/to/icon.png --w 24 --h 24 --colors 5 --out level.json
```

If you want to map the source pixels into a specific palette (keep the image structure, but restrict colors):

```bash
./scripts/py -m psld from-image path/to/icon.png --w 48 --h 48 --out level.json \
  --recolor-mode palette_map \
  --palette '#E63946,#457B9D,#2A9D8F,#F4A261,#8D99AE'
```

For grayscale images, `--palette-map-mode luma_buckets` often gives a nicer distribution:

```bash
./scripts/py -m psld from-image path/to/icon.png --w 48 --h 48 --out level.json \
  --recolor-mode palette_map \
  --palette '#E63946,#457B9D,#2A9D8F,#F4A261,#8D99AE' \
  --palette-map-mode luma_buckets
```

To avoid a single click creating a huge shooter, you can split oversized same-color components:

```bash
./scripts/py -m psld from-image path/to/icon.png --w 48 --h 48 --out level.json \
  --split-max-component 80 --split-mode cuts --split-cut-thickness 2
```

If your input is a black/white silhouette and you want the tool to paint it using a specific palette (ignore source colors entirely):

```bash
./scripts/py -m psld from-image path/to/icon.png --w 48 --h 48 --out level.json \
  --recolor-mode silhouette \
  --palette '#E63946,#457B9D,#2A9D8F,#F4A261,#8D99AE' \
  --recolor-color-mode radial_bands
```

`from-image` always writes a pixelized preview PNG next to `--out` by default:

```bash
./scripts/py -m psld from-image path/to/icon.png --w 48 --h 48 --colors 5 --out level.json --png-scale 12
```

To choose the preview path explicitly:

```bash
./scripts/py -m psld from-image path/to/icon.png --w 48 --h 48 --colors 5 --out level.json --out-png preview.png --png-scale 12
```

Notes:
- `psld from-image` requires `--out` to be a file path (not `-`), since the PNG preview is mandatory.
- `from-image` runs deterministic region/fragmentation validation by default. Disable with `--no-validate`.
- Transparent pixels stay empty (`null`) by default. If you want to fill them, add `--fill-background --background '#000000'`.
- Non-transparent pixels are quantized to `--colors` (median-cut).
- Very small color components can be merged into neighbors via `--min-component-size`.

## Export A PNG Preview

Requires `pip install -e ".[image]"`.

```bash
./scripts/py -m psld export-png level.json --out level.png
./scripts/py -m psld export-png level.json --layer top --out top.png
```

## Export Composite PNG (Top + Bottom)

Bottom layer (slots) is drawn as full cells, and top layer is drawn as smaller inset cells.

```bash
./scripts/py -m psld export-composite-png level.json --out composite.png --scale 16 --inset-scale 10
```

To add an outline around the inset top layer (off by default):

```bash
./scripts/py -m psld export-composite-png level.json --out composite.png --inset-outline
```

## Validate Fragmentation (Region Stats)

This computes connected components per color and can fail levels that are too fragmented.

```bash
./scripts/py -m psld validate level.json --min-largest-region 6 --max-fragmentation 0.08
```

To avoid huge trivial merges, add upper bounds too:

```bash
./scripts/py -m psld validate level.json --max-color-share 0.55 --max-largest-region 200
```

## Solve (Experimental)

Baseline deterministic BFS solver over tap actions (and optional wait ticks). This currently only works on small grids.

```bash
./scripts/py -m psld solve level.json --max-expanded 20000 --max-steps 60
```

## Generate From Prompt (Offline "Agent" Router)

This is an offline placeholder "agent" that routes prompts to known silhouettes when possible, otherwise renders text.

```bash
./scripts/py -m psld from-prompt "cat icon" --w 24 --h 24 --colors 5 --out cat.json
```

### Online LLM (OpenAI)

Set `OPENAI_API_KEY`, then:

```bash
./scripts/py -m psld from-prompt "sleeping cat icon" --provider openai --model gpt-4o-mini --w 32 --h 32 --colors 5 --out cat.json
```
