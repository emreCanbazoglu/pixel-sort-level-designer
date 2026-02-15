# Implementation Guide (Status + Next Tasks)

Date: 2026-02-15

This doc tracks what is implemented in this repo today, how to run it, and what remains to reach the end goal:

> Provide an image and deterministically produce a **game-ready level** (`level.json` + required previews) that is **solver-validated** (solvable + difficulty-scored).

## Principles

- Determinism first: image processing, validation, simulation, and solving must be deterministic.
- LLMs (if used) may propose masks/candidates; they must not manipulate pixels and must never bypass solver validation.
- Every generation stage should be callable, testable, and regression-safe.

## Current State

### What Works Now

**Image -> Level JSON + PNG previews**

- `psld from-image` converts an input image to a palette-index grid and writes:
  - `level.json`
  - preview PNG (mandatory; default next to `--out`)
- Deterministic processing (Pillow median-cut quantization, deterministic denoise).
- Deterministic gating (region/fragmentation checks) runs by default.

**Top/Bottom layers are different**

- `top` is the “picture” and also the mergeable tap layer.
- `slots` is derived deterministically from `top` with a strict constraint:
  - For every occupied cell `(x,y)`: `slots[y][x] != top[y][x]`
  - Color histogram is preserved (same total count of each color index), and the occupied mask is preserved.
- If strict mismatch is mathematically impossible due to a dominant top color (>50% of occupied cells), the generator performs a minimal deterministic “rebalance” seam cut on the dominant color to make the mismatch feasible, then derives `slots`.

**Preview tooling**

- `psld export-png` renders either `top` or `slots`.
- `psld export-composite-png` renders a composite:
  - bottom slots as full-size cells
  - top as smaller inset cells (outline off by default)

**Region stats validation**

- `psld validate` reports per-color connected components and can fail levels on:
  - min/max largest region size
  - max fragmentation (regions per occupied cell)
  - max per-color share of occupied cells
  - etc.

**Experimental simulator + solver CLI**

- `psld solve` exists (tick-based conveyor loop, BFS).
- This is currently **not a practical solver gate** for real grids (e.g. 48x48) and **needs rule alignment** with the new “top != slots” model (see Remaining Tasks).

### CLI Commands

```bash
./scripts/py -m psld -h
```

Main commands:

- `from-image` (writes `level.json` + required PNG preview)
- `from-text`, `from-word`, `from-prompt` (mask-driven generation)
- `export-png` (single layer)
- `export-composite-png` (top inset over slots)
- `validate` (region/fragmentation metrics)
- `solve` (experimental)

## Level Data Model (JSON)

Each generated level contains:

- `palette`: list of `#RRGGBB`
- `top`: `h x w` grid of palette indices (`int`) or `null`
- `slots`: `h x w` grid of palette indices (`int`) or `null`
- `forward_remove_order`: deterministic outer-to-inner exposure order (lane-reachability)
- `backward_place_order`: reverse of forward order
- `meta`: provenance + parameters (recolor mode, split settings, slot derivation stats, etc.)

## Image Processing Pipeline (Implemented)

Stages (deterministic):

1. Load image, downsample to target grid (currently `BOX` resampling).
2. Decide occupied mask:
   - `--mask-mode alpha` (default): use transparency threshold
   - `--mask-mode auto`: if no alpha, infer background from corners and threshold by `--bg-tol`
3. Color assignment to `top`:
   - `--recolor-mode source`: quantize source colors via median-cut to `--colors`
   - `--recolor-mode palette_map`: map source pixels into a provided palette
     - `--palette-map-mode nearest` or `luma_buckets`
   - `--recolor-mode silhouette`: paint the occupied mask using a palette distribution mode (ignores source colors)
4. Denoise: merge tiny connected components into neighbors (`--min-component-size`).
5. Optional split of oversized same-color components:
   - `--split-max-component N`, `--split-mode cuts|...`
6. Derive bottom slots:
   - strict mismatch + histogram preservation (max-flow)
   - optional top rebalance seam if needed for feasibility
7. Compute lane-reachability order from the occupied mask (outer-to-inner exposure).
8. Write:
   - `level.json`
   - preview PNG (mandatory)

## What’s Missing (Remaining Tasks)

### Phase 2: Deterministic Simulator + Solver (Critical)

To become a real gate, the simulator/solver must be updated to match the intended gameplay and scale.

**Rule alignment needed**

- Today `top` and `slots` differ per-cell.
- Shooter creation removes `top` cells immediately (per your rule).
- Shooter firing should affect `slots` only (and should not try to “remove corresponding top cells” by coordinate).

**Conveyor details still to encode precisely**

- Entrance behavior when the entrance position is already occupied:
  - reject tap?
  - queue?
  - multiple shooters can share a pos?
- Tick order details:
  - move then fire vs fire then move (currently configurable but needs to be fixed to the actual game)
- Shooter firing:
  - side+lane mapping must exactly match the in-game conveyor geometry.

**Make solving practical**

- BFS is too expensive on real boards.
- Next work is a solver that can run on real sizes with pruning + heuristics:
  - action filtering (avoid tapping components that can’t help soon)
  - state canonicalization and symmetry reduction
  - dominance pruning (ammo/exposed slots)
  - A*/IDA* with a meaningful lower bound
  - caps/timeouts with good failure explanations (why unsolved)

Deliverables:

- `psld solve level.json` that can handle target sizes in reasonable time.
- A golden set of solvable/unsolvable test levels (JSON fixtures).

### Phase 4: Difficulty Scoring

Once the solver is credible:

- define telemetry vector (solution length, branching, min conveyor slack, deadlock proximity, etc.)
- deterministic scoring function mapping telemetry to 1–10
- regression tests for scoring stability

### Agent Orchestration (Last)

Only after solver + scoring:

- batch generation (images -> variants -> gated -> export)
- catalog output folders (json + composite previews + metrics)

## Recommended Workflow Right Now

1. Generate from an icon/silhouette image.
2. Inspect the composite preview.
3. Iterate parameters (`--palette-map-mode`, `--min-component-size`, `--split-max-component`, validation thresholds).
4. Build a small golden set of images and expected outputs before major solver work.

