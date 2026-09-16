# Task EXT2: Task-keyed validation instead of a hard-coded check list
Status: todo
Depends on: S4 complete (the nine-point and side-wall checks must exist before they
can be registered as a reusable set)

Background: `docs/VALIDATION_ARCHITECTURE.md`.

## Goal
Which checks run is decided by the case's declared `intended_task` and by the
profile, not by which script happens to be executing. Generating something that is
not a box must not require writing a new test script.

## The problem today
`box_s2.py` hard-codes its check list. Every check it runs is either universal or
belongs to `place_object_inside`, but nothing says so, so none of it can be reused
by a different asset family without copying the file.

## Scope
1. **Check registry.** `src/parcel_forge/validation/registry.py`: each check declares
   an id, a tier (`universal` | `task` | `material`), and for tier `task` the
   `intended_task` values it serves. Registration is explicit, not by import magic.
2. **Profiles select check sets.** `profiles/*.json` gains a `required_checks` block
   naming tiers and task sets rather than relying on the runner. A profile that names
   a check which is not registered is an error, not a silent skip.
3. **Generic scene assembly.** Split `box_s2.py` into: build the asset (delegated by
   `asset_type`), place probes (delegated by the task's sampling strategy), run,
   judge (delegated by `intended_task`). The nine-point pattern becomes
   `sampling: nine_point` under `place_object_inside`, not a box feature.
4. **A second asset family as the proof.** A trivial one is enough -- an open
   cylinder or a tray -- purely to demonstrate that `place_object_inside` runs
   against it with no new check code. If that needs new checks, the split is wrong.

## Acceptance
- `pf box --all` produces identical verdicts to today for all six existing cases.
  This refactor must not change a single result; if it does, it broke something.
- A new asset family passes `place_object_inside` reusing the existing checks, with
  no new entries in the registry.
- A profile naming an unregistered check fails loudly.
- Every run's `validation.json` records which checks ran and why they were selected,
  so a skipped check is always visible.

## Explicitly not in scope
Rewriting `geometry.py` to be shape-generic. Per-family generators are the intended
design: `asset_type` selects the generator, `intended_task` selects the checks, and
those are deliberately separate fields.

## User learning
Concept: "what is this object" and "what is it for" are different questions, and
mixing them is what makes a test suite un-reusable. A cup and a crate share almost
nothing in shape and share almost every containment check.
Experiment: take `cases/open_box_normal.json`, change `intended_task` to something
the registry does not know, and confirm the run refuses rather than silently running
the box checks anyway.

## Next action
Write the registry with the existing checks registered into it, changing no
behaviour, and prove `pf box --all` gives byte-identical verdicts.
