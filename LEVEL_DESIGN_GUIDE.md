You are a senior game systems engineer and algorithm designer.

Your task is to implement an AI-assisted level generation pipeline for a deterministic puzzle game.

DO NOT produce placeholder architecture.
DO NOT simplify the solver.
Produce production-quality system design and code structure.

The system must prioritize correctness over novelty.

---

## GAME MODEL

The game is a deterministic merge-and-shoot spatial puzzle with these rules:

- Players merge adjacent same-colored blocks to create shooters.
- Shooter ammo equals merged block count.
- Shooters loop on a conveyor with capacity = 5.
- Shooters automatically fire at reachable matching slots.
- Slots clear from outer to inner layers.
- Level fails if conveyor is full AND no shooter can fire.
- Levels must ALWAYS be solvable.

No randomness is allowed in gameplay resolution.

---

## YOUR OBJECTIVE

Build a complete pipeline containing:

---

## Step-By-Step Execution Plan (Do Not Reorder)

This only works if later stages are gated by earlier deterministic validation.

### Phase 1 (Now): Image -> Grid

Goal: turn a meaningful silhouette image into a palette-limited grid we can ship and simulate.

1. Install image dependencies.
2. Run 20-30 real images through the pipeline.
3. Inspect results as both JSON and PNG previews.
4. Tune quantization + denoise until grids look clean:
   - 4-5 colors early
   - no single-tile noise
   - contiguous regions
   - background should not create a giant tappable merge (prefer empty/null background cells unless the design explicitly allows tapping background)
5. Save a small "golden set" of source images and expected grid outputs for regression tests.

Deliverables:
- `from-image` CLI producing `level.json` and `preview.png`
- a small sample set (source images + outputs) for repeatable testing

### Phase 2: Deterministic Simulator + Solver (Highest Leverage)

Goal: prove solvability and measure difficulty. Without this, generation is guessing.

1. Implement the forward deterministic simulator:
   - merge action (tap connected component)
   - shooter creation (ammo = merged size)
   - conveyor loop and capacity = 5
   - lane reachability logic (left/right = row, top/bottom = column; nearest reachable only)
   - auto-firing until stable
   - win/lose detection (full clear, or conveyor full + no shooter can fire)
2. Implement BFS or A* over player actions (tap choices).
3. Add pruning:
   - symmetric states
   - dominated actions / redundant micro-merges
   - impossible ammo vs remaining slots
4. Add a CLI command to run the solver on a JSON level and print metrics:
   - solvable yes/no
   - solution length (if solvable)
   - min conveyor slack
   - deadlock proximity
   - expanded states and runtime

Deliverables:
- `solve level.json` CLI
- a small suite of toy levels (solvable + deadlock) as tests

### Phase 3: Backward Slot Generation (Only After Solver Exists)

Goal: create slot layouts by backward construction and validate them with the solver.

1. Start from solved board and place slots inner -> outer.
2. Enforce lane reachability at placement time.
3. Reverse placement order to get playable removal order.
4. Run solver; reject if unsolvable.

Deliverables:
- `generate-slots --backward ...` producing slot grids + placement/removal order

### Phase 4: Difficulty Scoring (From Solver Telemetry)

Goal: difficulty 1-10 computed from real solver metrics.

1. Define telemetry vector from solver runs.
2. Create a deterministic scoring formula.
3. Validate against a small set of curated levels across targets.

Deliverables:
- `score level.json` CLI returning 1-10 + metric breakdown

### Phase 5: Agent Orchestration (Last)

Goal: scale content safely. AI/agent must never bypass solver validation.

1. Candidate proposal:
   - image-to-image variations (crop/scale/palette/denoise)
   - grammar recombination (templates)
2. Gate every candidate:
   - solver must find at least 1 solution
   - difficulty must be within target band
3. Export approved levels + previews.

Deliverables:
- `batch-generate` CLI that outputs a folder of solved, scored, previewed levels

---

### 1. Image → Grid Converter

Convert silhouette images into clean color grids.

REQUIREMENTS:

- Use deterministic color quantization (k-means or median cut).
- Limit early boards to 4–5 colors.
- Prevent single-tile noise.
- Favor contiguous regions.

Do NOT use an LLM for color mapping.

---

### 2. Bottom Slot Generator (CRITICAL)

Implement BACKWARD generation.

Process:

1. Start from an empty solved board.
2. Simulate filling slots from inner → outer.
3. Ensure each slot is lane reachable at placement time.
4. Record the reverse order as the playable puzzle.

Forward generation is NOT allowed.

---

### 3. Deterministic Solver (MANDATORY)

Implement a state-search solver.

Minimum requirements:

- BFS or A\* search
- State must encode:
  - remaining slots
  - shooter ammo
  - conveyor occupancy
  - reachable lanes

PRUNING:

- symmetric board states
- redundant micro-merges
- impossible ammo states

Goal:
Detect existence of at least ONE solution path.

Solver must run automatically on generated levels.

Reject unsolvable boards.

---

### 4. Difficulty Scoring Engine

Compute difficulty using telemetry from solver runs.

Metrics should include:

- solution length
- branching factor
- minimum conveyor slack
- deadlock proximity
- ammo tightness
- unlock depth

Output a normalized difficulty score from 1–10.

Do NOT guess difficulty heuristically.

Use solver data.

---

### 5. Level Grammar System

Implement reusable templates such as:

- ring unlock
- corridor access
- dual-front attack
- layered core
- false freedom

The generator should recombine grammars rather than produce chaotic boards.

---

### 6. AI Usage Boundaries

AI may assist ONLY in:

- proposing silhouette candidates
- clustering difficulty
- detecting interesting board patterns

AI must NOT override solver validation.

---

## OUTPUT REQUIREMENTS

Produce:

1. System architecture
2. Data models
3. Solver pseudocode
4. Generator pseudocode
5. Difficulty formula
6. Suggested tech stack
7. Performance considerations
8. Example level pipeline
9. Failure case handling

Favor clarity over verbosity.

Avoid theoretical discussion.

Design this like it will ship.

---

## Repo Status (2026-02-15)

This file is the target spec. For current implementation status and remaining tasks, see:

- `IMPLEMENTATION_GUIDE.md`
