# Marvel Crisis Protocol Dice Simulator — Build Plan

**Goal:** Input attack/defense dice pool sizes and special rules, simulate a statistically
significant number of attacks with an adaptive "smart player" applying modifications, and
save outcomes for analysis.

**Environment:** Build and prototype locally in Jupyter. Port to Databricks (Python + SQL)
once the core engine works, fitting into the existing `mcp.game` Unity Catalog schema.

**Approach:** Brad writes the code; this plan scaffolds it in stages, smallest-safe-step
first, so architectural decisions (especially the rule contract) get made before they're
expensive to change.

---

## Rule Categories (established during design, used throughout)

Special rules fall into three distinct categories — keeping them separate avoids folding
one kind of rule into a contract shaped for another:

1. **Active modifications** — something a player *does* to a die during a modification
   window (Pierce, Cover, rerolls). Contract: `window`, `target`, `mode`
   (deterministic/probabilistic), `uses` (fixed/unlimited/scaling).
2. **Passive scoring modifiers** — always-on reweighting of a die's value for tallying
   (Count Wild as 2 Successes, Special Forces). Contract: which face, and the effect
   (reclassify success/failure, set value to N, import an opponent face count into your
   own total).
3. **Restrictions/permissions** — disable an entire modification window for a character
   (e.g. "Defender can't modify their own dice"). Contract: owner, disabled window(s).

Passive modifiers matter beyond tallying: when an active modification lets a player choose
*which* die to target among several eligible ones (e.g. Pierce), that choice should be
value-aware — pick the die whose removal changes the net total the most, accounting for any
passive reweighting currently in effect. This is why success tallying is built as a
**per-die value lookup, then sum**, rather than a hardcoded face count — the same lookup
gets reused later for target selection.

A related but distinct complexity showed up in the Criticals/explode step (step 5): some
character rules change *which faces explode* or *how many bonus dice an explosion grants*
(always-on parameters, similar in spirit to passive modifiers but scoped to the explode step
rather than the success tally), while others (The Grand Illusion) **transform the roll's
actual contents** before a step runs, rather than reweighting how existing dice are read.
That's a fourth, distinct kind of effect — a pre-step transformation, timing-sensitive by
nature — worth keeping separate from the three categories above rather than forcing it into
one of them.

---

## Stage 1 — Core dice model ✅ done

- `DieFace` dataclass (PascalCase per PEP8 class-naming convention), `frozen=True` (fixed
  rule constants — immutability catches accidental mutation of a shared instance).
- Fields: `name`, `attack_value`, `defense_value`, `dodge_value` (ints, not booleans — a
  face's value defaults to 1 for a plain success, 0 for a failure, but needs to support
  higher values once passive modifiers like "Count Wild as 2 Successes" exist), plus
  `is_modifiable` (bool — genuinely a yes/no fact, no magnitude to represent, stays a bool)
  and `quantity` (physical copies of this face on the 8-sided die).
- Six instances (Critical, Wild, Hit, Shield, Blank, Skull) collected into one list,
  `all_faces`, which is the single source of truth — both the sampling list and the lookup
  dict derive from it rather than being hand-typed separately:
  ```python
  all_faces = [hit, critical, wild, shield, blank, skull]

  mcp_dice = []
  for face in all_faces:
      mcp_dice.extend([face.name] * face.quantity)

  face_lookup = {}
  for face in all_faces:
      face_lookup[face.name] = face
  ```
- Roll function: `random.choices(mcp_dice, k=pool_size)`.

## Stage 2 — Success tallying (no rules) ✅ done

- Per-die value lookup, then sum, rather than a hardcoded count of specific face names —
  `face_lookup[result].attack_value` per die, summed for the total. With no passive rules
  active this returns the same numbers a hardcoded count would, but it's already a hook
  passive modifiers can plug into later without a rewrite.
- Net successes = attacker total − defender total; hit/damage determined from that net value
  (≤0 is a failure, >0 hits for that much damage).
- Known follow-ups, not yet done:
  - Convert this logic into a function (e.g. `resolve_attack(attacker_roll, defender_roll)`)
    that returns results rather than printing them — needed by Stage 3's combination step,
    the Stage 7.5 experiment harness, and the Stage 11 simulation loop, all of which need to
    call this repeatedly rather than re-running notebook cells.
  - Keep "net successes" (can be negative) and "damage" (never negative) as distinct values
    once storage design (Stage 12) comes up — `net_damage` currently does double duty as
    both, which is fine for the `if` logic as written but worth separating before it's
    persisted anywhere.

## Stage 3 — Criticals step ✅ done (plain version)

- One bonus die rolled per Critical in the **original** roll (not the combined roll) — this
  is what makes "Criticals only explode once" correct by construction (the explode-pool size
  is computed before the original roll is combined with the bonus dice), rather than needing
  an explicit recursion guard.
- The bonus-dice-per-explosion count is pulled out as a named field on `DieFace` (currently
  `explode_into`, defaulting to 0, set to 1 for Critical) rather than hardcoded — so a future
  character who explodes into 2 dice per Critical is a data change, not a rewrite.
  - Naming follow-up: rename `explode_into` to something like `bonus_dice` or
    `explosion_count` — "explode into" reads as if the face transforms into another face
    (which is literally what The Grand Illusion does), and having two different mechanisms
    sound alike will get confusing once Grand Illusion is implemented.
- Combining original and bonus rolls: use `+` to build a new list
  (`attacker_full_roll = attacker_original_roll + attacker_explode_roll`), not `.extend()`,
  which mutates a list in place. Keep all three lists — original, exploded, and full — as
  separate named lists per side, rather than merging in place or nesting into a list of
  lists:
  - Avoids the "re-run this cell and silently double-count the bonus dice" footgun that
    in-place mutation creates.
  - List-of-lists was considered and rejected — the number of "waves" per side is always
    exactly 2 (original + one explosion round, since explosions don't recurse), so there's
    no variable-length grouping that would justify the extra unwrapping step.
  - Preserves the original-vs-exploded distinction for potential later analysis (e.g. "how
    often do exploded dice swing the result") that would be lost if merged immediately.
  - Rename `attacker_roll` → `attacker_original_roll` at this point, since `attacker_roll`
    no longer unambiguously means "the roll" once a `_full_roll` also exists.
- **Three character-specific rules identified for later, not implemented yet** — noted here
  so Stage 3's plain version stays deliberately extensible rather than needing rework:
  1. Some characters add 2 bonus dice per Critical instead of 1 (parameter change to
     `explode_into`/`bonus_dice`).
  2. Some characters can count a capped number of Skulls as Critical, for both success and
     exploding purposes — more sweeping than a typical passive modifier, since it reclassifies
     a face's identity for two purposes at once rather than just adjusting a value.
  3. **The Grand Illusion** transforms all Criticals into Skulls *before* the explode step
     runs — a genuinely different mechanism (mutates roll contents, not a property lookup),
     and order-sensitive: if a character with rule #2 above were ever in play alongside Grand
     Illusion, the order these two effects run in would change the outcome. Worth deferring
     entirely until the rule contract (Stage 4) can represent transformation-with-timing
     explicitly, rather than forcing it into the explode-eligibility/bonus-dice-count shape
     used for the other two rules.

## Stage 4 — Define the rule contract

- Formalize the three rule-category shapes described above (active modification, passive
  modifier, restriction) before writing more than one or two rules.
- Extend thinking to cover the Stage 3 findings: passive-modifier-like parameters scoped to
  steps other than success tallying (explode eligibility, bonus dice count), and a distinct
  shape for pre-step roll transformations with explicit timing (Grand Illusion).
- No decision engine yet — just agree on the data every rule of each type needs to expose.

## Stage 5 — Implement 1–2 simple deterministic rules

- Pick two low-complexity, non-scaling active modifications (Cover, Pierce) and implement
  them mechanically: "given a specified die, do X." No decision-making about *whether* or
  *which* die yet — that's Stage 6.
- Confirms the Stage 4 contract shape is actually usable in code.

## Stage 6 — First decision engine (scoped to the 2 rules above)

- Given current pool state and legal rules for a window, decide which to apply.
- Core heuristic: prefer deterministic modifications over probabilistic ones when they fully
  cover the failures present (the original reroll vs. guaranteed-success example).
- For modifications involving a choice among multiple eligible dice (Pierce), select using
  the per-die value function from Stage 2 — accounts for passive modifiers automatically, no
  special-casing.

## Stage 7 — Add a probabilistic rule

- Bring in a reroll-type rule (Reroll Any) alongside the two deterministic rules from Stage 5.
- Stress-tests whether the Stage 6 decision logic actually generalizes, while it's still
  cheap to fix.

## Stage 7.5 — Experiment harness

- Once at least two comparable probabilistic modifications exist (e.g. Reroll All vs.
  Reroll 2), build a harness that runs a *fixed* starting dice state through multiple named
  policies and compares outcome distributions — e.g. sweep "number of existing successes"
  from 0 upward under each policy to find the tipping point where Reroll All stops being
  favorable versus Reroll 2.
- Requires: (a) the decision engine structured as a swappable policy/strategy parameter
  rather than hardcoded conditionals, so different policies can be injected and compared;
  (b) resolution functions that accept a pool as input independent of how it was generated,
  so a fixed test state can be fed in instead of a fresh random roll.
- Reusable for later tipping-point questions (scaling rules, opponent-targeting rules) as
  they come up — not a one-off built just for the reroll case.

## Stage 8 — Add opponent-targeting rules

- Introduce a rule from the attacker-modifies-opponent or defender-modifies-opponent windows
  (Oscorp Weaponry, Witty Banter).
- Tests whether the engine correctly separates "modify my own dice" incentives (remove
  failures) from "modify opponent's dice" incentives (remove successes).

## Stage 9 — Add scaling rules

- Bring in a rule whose potential depends on pool state (Warrior of Legend, Death Dancer,
  Energy Absorption).
- Real test of whether the "uses: scales with X" contract field was designed well.

## Stage 10 — Fill out the remaining rule catalog

- With the engine proven against a representative case from each category, remaining rules
  become largely mechanical implementation against the existing contract. Includes the three
  Criticals-step character rules deferred from Stage 3.

## Stage 11 — Simulation loop

- Wrap one resolved attack into a function; run it N times with fixed pool sizes and rule
  sets, collecting results (hit/miss, damage dealt, which rules fired).
- Decide sample-size approach: fixed large N vs. running until a confidence interval
  tightens.

## Stage 12 — Outcome storage schema

- Design the result schema (one row per simulated attack, or per simulated event within an
  attack?). Keep net successes and damage as distinct fields (see Stage 2 follow-up).
- Worth sketching in SQL DDL terms even while still in Jupyter, since it shapes what the
  Python result objects need to serialize into.

## Stage 13 — Port to Databricks

- Move the notebook over; swap local result storage for a Delta table fitting the existing
  `mcp.game` schema conventions.
- Decide whether the simulation runs as a notebook job or gets wrapped as a callable
  procedure, consistent with the existing stored-procedure conventions on the platform.
