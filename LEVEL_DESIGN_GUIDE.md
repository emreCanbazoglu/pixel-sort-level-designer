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
