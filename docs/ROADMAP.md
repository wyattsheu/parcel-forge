# Roadmap (S0-S7)

Authority: `IsaacSim_From_Zero_Start_Here.md` section 5 defines S0–S7.
User-approved upstream adoption (D037, docs/UPSTREAM_ADOPTION_PLAN.md) revises S5–S7 execution.
`IsaacSim_Asset_Workflow_Handbook.md` (M0-M9) is consulted for technical detail
only; we do not run a second parallel schedule.

Status values: `todo`, `in_progress`, `done (verified)`, `blocked`.
A stage is only `done (verified)` when its required evidence exists under `runs/`.

| Stage | Scope | Required evidence | Status |
| --- | --- | --- | --- |
| S0 Project & environment | New repo, entry rules, progress files, read-only inventory, doctor | Real versions/paths, known-good launch method | done (verified) — see docs/STATE.md |
| S1 Minimal simulation | Ground + cube, finite steps, pose read-back, PNG | Command, exit code, trajectory, PNG, run manifest | done (verified) — see docs/STATE.md |
| S2 Fixed open box | Bottom + 4 walls per handbook section 7, centre probe drop | Results for normal box, sealed-lid fault, missing-bottom fault | done (verified) — suite table in runs/ |
| S3 Parameterisation & static validation | JSON schema, dimension/thickness rules, USD read-back, 10 cases | Input-to-output hashes, dimensions, error classification | done (verified) — 13 cases, S3 suite table in runs/ |
| S4 Physics & coverage | Dynamic box, mass and inertia, nine-point drop, side-wall tests | Maths cross-check, dynamic trajectories, settling and collision checks | done (verified) — readback, explicit contacts, 9/9 placement, 4/4 walls, dynamic settling and fault regression; CCD disabled, render separate |
| S5 Upstream integration & repair | S5-A pinned baseline → B evidence adapter → C recording → D agent repair; E BYOR when needed | upstream example, normal/fault gates, exact recordings, bounded repair | in_progress — S5-A/B/C verified; D v2 two fresh repair chains and visual-state recovery measured; physics resume unsupported; JSON exchange verified, live model pending |
| S6 Batch & semantics | Natural language to spec, batch driver, multi-view VLM | Per-case inputs, model/prompt versions, cost, verdicts | todo |
| S7 Handover delivery | Normal + fault test sets, retained cases, cold-start handover | Minimal reproduction commands, result table, versions and limits | todo |


## Stage gate for S4

Do not start S4 until both suites reproduce on fresh runs:
`./scripts/pf verify --all` (13 cases, ~4 s, no GPU) and
`./scripts/pf box --all` (6 cases, ~2.5 min, GPU).

## Extensions beyond S0-S7

| card | scope | gate |
| --- | --- | --- |
| docs/tasks/EXT1_cardboard_flaps.md | RSC flaps, crease lines, elastic-then-plastic fold behaviour | after S4 (D017 now resolved); rigid-hinge proxy diagnostics verified 2026-09-17, full material calibration/orthotropic panels pending |
| docs/tasks/EXT2_task_keyed_validation.md | checks selected by `intended_task`, so a non-box asset reuses them | after S4 |

Background: `docs/research/CARDBOARD_MECHANICS.md` (sources) and
`docs/VALIDATION_ARCHITECTURE.md` (how checks generalise beyond one asset).
The current asset is a rigid open tub with a real cavity -- a valid fixture for
"can a robot place an object inside a box", and not a cardboard box. No report may
imply otherwise.

## Explicitly out of scope right now

Isaac Lab, MCP, ROS, databases, Blender, CadQuery, Pydantic schemas, LLM/VLM
calls and any training pipeline. Upstream-required dependencies belong only in its isolated environment. Each is added only when a task card needs it,
with a decision record explaining why.

## 2026-09-18 泛用工作流實作拆分（局部實作與驗證）

[完整主計畫](plans/2026-09-18_general_asset_workflow_master_plan.md) 將 S5/S6/S7 與 EXT2 拆成有界 P0–P5 卡，並非另一套平行里程碑。
[WF-P0](tasks/WF_P0_contracts_and_capabilities.md)離線完成；WF-P1部分完成；[圖片基線WF-P3A](tasks/WF_P3A_image_backend.md)真生成/剛體physics/cold-load完成，人工形狀/材料校準待確認。現有 S0–S7／EXT1 狀態不變。

WF-P4 雙入口/共用Skill/可攜設定與私人GitHub交付有界完成，見tasks/WF_P4_portable_entry.md。文字自動authoring、5090執行與通用資產工作流仍未完成，不將S6/S7整體標為done。
