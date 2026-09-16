# How validation generalises beyond one box

Written 2026-09-16 in answer to a direct question: the S4 tests (nine-point drop,
side-wall blocking, contact settings) look like cardboard-box tests. If the next
thing generated is not a box, does the whole test suite have to be rewritten? And
how does NVIDIA's usd-content-agents, which clearly does not generate only one
object, handle this?

## The short answer

The nine-point drop is **not** a cardboard-box test. It is a **containment test**,
and it applies to anything whose job is to hold something: a bin, a tray, a crate, a
cup, a tote, a drawer. What makes it run is not the shape of the asset but its
declared purpose.

That purpose already exists in this project's schema, and has since S3:

```json
"asset_type": "open_box",
"intended_task": "place_object_inside"
```

`intended_task` is a required field. What is missing is the code that reads it and
selects checks from it. Today the check list is hard-coded in `box_s2.py`. That is
the actual gap, and it is a small one.

## Three tiers of check

The useful split is not by shape. It is by **what the check depends on**.

### Tier 1 — universal: runs on every asset, whatever it is

Nothing here knows or cares what the object is.

| check | where it lives now |
| --- | --- |
| stage opens, no missing references | `validation/static_usd.py` |
| `defaultPrim` set, metersPerUnit, kilogramsPerUnit, upAxis | same |
| dimensions read back from output geometry match the spec | same |
| collider / rigid-body hierarchy is sane, no nested rigid bodies | same |
| mass finite and > 0; inertia positive definite and satisfies the triangle inequalities | `mass_properties.py` |
| NVIDIA's own 41-rule asset validator | `validation/official_usd.py` |
| no NaN, finite step budget, clean shutdown | `box_s2.py` |
| the validator itself can still fail (G7) | `validation/official_usd.py` |

This tier is already generic. It would run unchanged on a mug, a pallet or a robot
gripper.

### Tier 2 — task/affordance: selected by `intended_task`

This is where the nine-point drop actually belongs.

| `intended_task` | what gets checked | applies to |
| --- | --- | --- |
| `place_object_inside` | probe reaches the interior floor; multi-point coverage across the opening; walls block a sideways approach; nothing falls through | box, bin, tray, cup, tote, crate |
| `grasp` | approach poses reachable; closure achieves contact; object survives a lift | almost anything |
| `stack` | load-bearing without collapse; toppling margin | boxes, crates, pallets |
| `pour` / `empty` | contents leave through the intended opening only | cup, bottle, hopper |
| `articulate` | joint range, drive response, no self-intersection through the range | lids, doors, flaps |

Judging is already written in a shape-independent way: `validation/outcome.py` takes
a resting position **in the asset's local frame** plus the cavity dimensions. Nothing
in it mentions cardboard, walls or plates. Point it at a cup's cavity and it works.

### Tier 3 — material/shape specific: the genuinely narrow layer

Crease yield for corrugated board (`docs/research/CARDBOARD_MECHANICS.md`),
handle thickness for a mug, hinge friction for a specific latch. This is the only
tier that has to be rewritten per object family, and it is deliberately the smallest.

## What NVIDIA does, as far as their public material shows

From their repo and its agentic README (read 2026-09-16, see `docs/METHODS.md`):

- Generation is split into **capability agents** -- Geometry, Material, Texture,
  Physics, Joint -- plus a separate **Validation Agent** that "evaluates USD,
  renders, and simulation evidence against deterministic and model-assisted checks".
- Validation has two entry points: `content-workflow-cli validate run`, described as
  validating "against **tasks** and reference evidence", and
  `content-workflow-cli simready validate-profile` for profile conformance, with a
  `simready conform-profile` repair path.
- Benchmarking uses "versioned asset cases and durable evidence rather than relying
  only on a final image or a single aggregate score".

The word that matters is **tasks**. Their validation is keyed to what an asset is
for and to a named profile, not to a per-object bespoke test script. That is the
same shape as the three tiers above, and it is why this project's `profiles/`
directory and `intended_task` field exist at all.

What their public material does not show is the internals of how checks are
registered and selected. The tiering here is this project's design, informed by
theirs; it is not a claim about their implementation.

## The concrete change this implies

Small, and it does not invalidate anything already built.

1. **A check registry.** Each check declares the tier it belongs to and, for tier 2,
   which `intended_task` values it serves. A profile names the checks it requires.
2. **Profiles select, they do not define.** `profiles/open_box_v1.json` becomes
   "tier 1, plus the `place_object_inside` set, with these tolerances". A cup profile
   reuses the same `place_object_inside` set with different dimensions.
3. **Scene assembly gets a generic path.** Today `box_s2.py` builds a box and drops a
   probe. It should become: build the asset (whatever it is) + place probes according
   to the task's sampling strategy. The nine-point pattern is a *sampling strategy for
   a containment task*, not a property of boxes.
4. **`asset_type` picks the generator, `intended_task` picks the checks.** Those are
   two separate decisions and the schema already keeps them in separate fields.

Recorded as `docs/tasks/EXT2_task_keyed_validation.md`.

## What this means for the work already done

None of it is wasted, and none of it is box-shaped by accident:

- `geometry.py` is a generator for one asset family, as intended. A second family
  gets a second generator, not a rewrite.
- `mass_properties.py` is fully generic: it takes a list of plates with sizes and
  centres. Any assembly of boxes works; a mesh-based asset would need a different
  volume integrator, which is a new function, not a change to this one.
- `validation/outcome.py` and `validation/static_usd.py` are already tier 1 and 2,
  written without reference to cardboard.
- The evidence machinery -- run directories, manifests, hashes, profiles, exit codes
  -- is entirely asset-agnostic.

The part that is currently box-shaped is the *wiring*: `box_s2.py` hard-codes which
checks run. That is the file EXT2 changes.
