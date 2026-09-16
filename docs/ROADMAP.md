# Roadmap (S0-S7)

Authority: `IsaacSim_From_Zero_Start_Here.md` section 5 defines this schedule.
`IsaacSim_Asset_Workflow_Handbook.md` (M0-M9) is consulted for technical detail
only; we do not run a second parallel schedule.

Status values: `todo`, `in_progress`, `done (verified)`, `blocked`.
A stage is only `done (verified)` when its required evidence exists under `runs/`.

| Stage | Scope | Required evidence | Status |
| --- | --- | --- | --- |
| S0 Project & environment | New repo, entry rules, progress files, read-only inventory, doctor | Real versions/paths, known-good launch method | done (verified) — see docs/STATE.md |
| S1 Minimal simulation | Ground + cube, finite steps, pose read-back, PNG | Command, exit code, trajectory, PNG, run manifest | done (verified) — see docs/STATE.md |
| S2 Fixed open box | Bottom + 4 walls per handbook section 7, centre probe drop | Results for normal box, sealed-lid fault, missing-bottom fault | todo — card at docs/tasks/S2.md |
| S3 Parameterisation & static validation | JSON schema, dimension/thickness rules, USD read-back, 10 cases | Input-to-output hashes, dimensions, error classification | todo |
| S4 Physics & coverage | Dynamic box, mass and inertia, nine-point drop, side-wall tests | Maths cross-check, dynamic trajectories, settling and collision checks | todo |
| S5 AI repair | Agent repairs spec/generator from findings, max three attempts | before/after, patch, new test results | todo |
| S6 Batch & semantics | Natural language to spec, batch driver, multi-view VLM | Per-case inputs, model/prompt versions, cost, verdicts | todo |
| S7 Handover delivery | Normal + fault test sets, retained cases, cold-start handover | Minimal reproduction commands, result table, versions and limits | todo |

## Stage gate for S2

Do not start S2 until `./scripts/pf smoke` reproduces on a fresh run and
`docs/STATE.md` still matches the newest run under `runs/`.

## Explicitly out of scope right now

Isaac Lab, MCP, ROS, databases, Blender, CadQuery, Pydantic schemas, LLM/VLM
calls and any training pipeline. Each is added only when a task card needs it,
with a decision record explaining why.
