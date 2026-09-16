# Methods adopted from published work

Source for this list: `IsaacSim_Asset_Workflow_Handbook.md` section 3. That table
names the sources; this file records, for each one, **the specific mechanism we
read**, **what we implemented**, **where it lives**, and **what we deliberately did
not take**. Anything not yet implemented is marked as such and points at a task card.

Read on 2026-09-16. Each summary below comes from the source itself, not from
recollection.

---

## 1. NVIDIA USD Content Agents — workflow/tool separation, run evidence, validation entry point

Repo: https://github.com/NVIDIA-Omniverse/usd-content-agents

**Mechanism read.** Four layers: a coding-agent runtime that interprets intent and
reviews evidence; skills that own capability policy; workflows that own run state
and checkpoints; and *typed tools* that perform deterministic operations
(`usd-cli`, `material-agent`, `physics-agent`, `validation-agent`). Every run writes
a self-contained directory:

```
inputs/  request.json  workflow_state.json  decisions/
artifacts/  renders/  validation/  traces/  summary.md
```

Requests are digest-bound; changing an input requires a new run rather than editing
an old one. Validation entry points: `content-workflow-cli validate run` and
`content-workflow-cli simready validate-profile`, with a `simready conform-profile`
repair path. Their stated goal: "a visually plausible output cannot hide an
incomplete workflow."

**Adopted.**
- Workflow/tool separation: `pf` subcommands are the tools; `*_host.py` modules own
  run state and evidence. Geometry, schema, authoring and validation never import
  each other's concerns.
- Per-run directory, append-only: `runs/<timestamp>_<kind>/`.
- Digest binding: every `manifest.json` carries the code commit plus a dirty-diff
  hash, `inputs_sha256`, `asset_sha256` and `profile_sha256`.
- Failed and aborted runs are retained (`aborted.json`), never overwritten.
- **Their validator, actually running.** `omni.asset_validator.core` ships inside
  this Isaac Sim install and imports without Kit. `pf verify` now runs its 41 rules
  on every built asset: `src/parcel_forge/validation/official_usd.py`. Internal G1
  rules and NVIDIA's rules are counted as **separate coverage** in `validation.json`.

**Not adopted.**
- Their services and CLIs are not installed here, and the handbook says not to
  assume they are. We took the architecture and the validator, not the deployment.
- No SimReady profile is requested or claimed. `validation.json` says so in writing.

**Not yet implemented** — `workflow_state.json` (phase + resume information),
`decisions/` (structured agent choices, needed once S5 exists), `traces/` (per-tool
execution records; today we keep raw `logs/`), and typed tool declarations. See D010.

---

## 2. Articulate-Anything — actor–critic over evidence, and its failure mode

Paper: https://arxiv.org/html/2410.13882v2

**Mechanism read.** A vision-language *actor* emits high-level Python that compiles
to URDF. A *critic* sees the source code plus evidence — images for link placement,
**video of the predicted joint moving in simulation** for joints — and returns a
textual assessment plus a 0–10 realism rating used as a proxy loss. The loop runs
while the rating is on the wrong side of a threshold of 5. Iterative refinement
bought about **5.8%** on link placement.

Their reported failure mode is the important part: *"The largest disagreement comes
from false positive case i.e., the critic falsely declares an incorrect articulation
as correct. These cases include difficult-to-notice errors."*

**Adopted (as binding design rules for S5/S6).**
- The repair actor edits the **specification or the generator**, never the USD
  output directly — matching "code, not geometry" and keeping every change replayable.
- Evidence of *motion*, not just a final frame, is what a critic may judge. Our S2
  runs already store the full `trajectory.csv`, and a critic gets the trajectory and
  the numeric verdict, not only a render.
- **A model-based critic may never upgrade a verdict.** Deterministic checks own
  pass/fail. The critic can only (a) propose a repair, or (b) downgrade a
  deterministic pass to "needs human review". A false-positive critic then costs a
  wasted iteration, not a wrong pass. This directly answers their failure mode.
- Bounded iterations with a recorded stopping reason (the handbook's limit of three).

**Not adopted.** A numeric "realism rating" as the acceptance signal. Our acceptance
is the measured resting position in the box local frame; a 0–10 opinion is at most
a triage hint, never a gate.

---

## 3. LL3M — assets as code, version-matched documentation retrieval

Paper: https://arxiv.org/html/2508.08228v1

**Mechanism read.** Assets are Python for Blender's `bpy` API, kept modular and
editable rather than baked meshes. A retrieval agent queries a RAG database built
from 1,729 official **Blender 4.4** documentation files, giving the coding agent
version-specific knowledge; the authors report this **reduced error rates by 26%**
and allowed a 5× increase in complex operations. Refinement runs planner → retrieval
→ coder, then a critic over 5 rendered views, then a *verification agent* that
confirms the fix was actually applied.

Reported failure modes: VLMs misplace objects spatially (3–4 follow-up prompts for
spatial tasks), and **refinement agents rewrite whole scripts instead of making
localized edits when they lack shared context.**

**Adopted.**
- Asset as code: `geometry.py` + `usd_author.py` are parameterised, readable and
  unit-tested; the USD file is an output, not the source of truth.
- Version-matched API knowledge, the hard way: this install is Isaac Sim 6.0.1,
  where `isaacsim.core.api` no longer exists, so the adapter was written from the
  local `site-packages` source rather than from 4.x tutorials (D002). LL3M's result
  is the argument for making that a *tool* rather than a habit — see D011.
- Their "verification agent" separation becomes a rule for S5: *"was the change
  applied"* and *"did the change fix the problem"* are two distinct checks with two
  distinct records.

**Not adopted.** Blender/`bpy` as the authoring backend, a RAG service, and treating
visual quality as a quality signal: a good-looking box tells us nothing about whether
it can hold an object.

---

## 4. Scalable Real2Sim — what physical parameters can honestly be claimed

Paper: https://arxiv.org/html/2503.00370v2

**Mechanism read.** Inertial parameters are identified from robot joint-torque data
in two stages: identify the arm empty, then identify it grasping the object, and take
the difference using lumped-parameter linearity, with a **pseudo-inertia
positive-definiteness constraint** keeping the result physically feasible. Excitation
trajectories are optimised for information gain.

Their accuracy, on benchmark objects:

| quantity | error |
| --- | --- |
| mass | 1.34% ± 0.21% |
| centre of mass | 2.15% ± 1.20% |
| **rotational inertia** | **42.35% ± 15.64%** (one object: 358.6%) |

**Adopted (binding for S4).**
- **Parameters get confidence tiers, not one undifferentiated number.** Mass and COM
  from geometry are `derived_exact` (a formula over a known shape). Anything claimed
  about a real cardboard box would be `estimated`. Nothing in this project is
  `measured`, and no run may say so.
- **Inertia is the least trustworthy quantity in the pipeline.** Even with torque
  sensors, published error is ~42%. So: S4 compares PhysX's inertia read-back against
  our closed-form tensor with an explicitly looser tolerance than mass, and the report
  states that agreement with our own formula is *not* evidence about a real box.
- **Physical-feasibility check, adopted directly:** the inertia tensor must be
  positive definite and satisfy the triangle inequalities
  (Ixx + Iyy ≥ Izz and permutations). This is cheap, deterministic, and catches
  authored tensors that no rigid body could have. See `docs/tasks/S4.md`.

**Not adopted.** Torque-sensor identification, excitation-trajectory optimisation, and
any claim that a name or a photograph implies real mass or friction.

---

## 5. EmbodiedGen · Kit USD Agents · OpenAI ExecPlan

- **EmbodiedGen** (https://github.com/HorizonRobotics/EmbodiedGen): kept as a future
  *input*. When an externally generated asset arrives, it enters the same
  `pf verify` / `pf box` gates as ours. A generator calling itself sim-ready does not
  skip acceptance. Not implemented; relevant from S7.
- **Kit USD Agents** (https://github.com/NVIDIA-Omniverse/kit-usd-agents): an option
  for version lookup and tool entry points. MCP remains **not** a first-phase
  requirement, and nothing here depends on it.
- **OpenAI ExecPlan** (https://developers.openai.com/cookbook/articles/codex_exec_plans):
  task cards are self-contained — goal, scope, acceptance, evidence, failure routing,
  current findings and one next action — so a session with no prior conversation can
  pick one up. Implemented in `docs/tasks/*.md` and `AGENTS.md`. We do not rely on a
  magic filename to auto-trigger anything.

---

## Standing rule

Every row above is a *method*, not a dependency. Nothing in this table justifies
installing a service, and no source's approval substitutes for this project's own
evidence: a claim is verified when a command ran, exited, and its output is saved
under `runs/`.
