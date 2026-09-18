# S5-D: Bounded spec repair with official validation
Status: in_progress.
Depends on: S5-A/B/C verified.

Keep JSON spec repair and ITRI gate external: pinned upstream has no generic
spec-repair plug-in. Reuse actual focused prepare/check/finalize and supported
checkpoint interfaces. Never modify probe/task/expected_outcome/profiles or
acceptance rules to pass. Controller v2 receipts enforce max three submissions
per original source, including rejected reserved submissions.

Verified: two historical hand-authored repairs, proposal source/budget/path gate,
background hardening offline, schema parity and hash linkage. Fresh v2
missing-bottom candidate physics rerun plus link/focused gate verified:
runs/20260917T062811Z_s2_open_box_no_bottom,
runs/20260917T062915Z_s5d_repair_link,
runs/20260917T062920Z_s5d_focused_gate.

Template limitation measured: physics_sane official Wave 2 resume unsupported.
render_valid controlled interruption/CLI recovery state test passes at
runs/20260917T062716Z_s5d_resume_check, while final render verdict remains fail
because isolated OVRTX intentionally unavailable. Not physical/model recovery.
Full actor/model execution remains pending. Landlock content-write probes are
not complete read/network/process/metadata/FD isolation. No model shell yet.
121 tests (7 skipped) pass: runs/20260917T062951Z_s5d_resume_final_checks.

Second fresh v2 sealed chain verified: 20260917T064636Z_s2_open_box_sealed; link/focused exit 0.
Explicit manual stage restart policy: docs/REPAIR_RESTART_POLICY.md.

Acceptance remaining: safe JSON-only
actor/model proposal with exact prompt/output; model execution evidence; no invented native hook or validator replacement.
JSON-only file prompt/response exchange now verified, no model tools or API calls.
124 tests (7 skipped) exit 0: runs/20260917T071800Z_proposer_exchange_tests.
Exact prompt and hand-authored fixture response archived; live model still not_tested.
User says paused viewer OK; underlying GPU crash cause unresolved.
README keyboard example alignment reviewed; official geometry dry-run on existing box
exit 0: runs/20260917T073054Z_upstream_geometry_plan. Not new text generation.
Box provider goal: contracts/box_generation_goal.txt; provider still unconfigured.
This qualifies an upstream interface within S5-D; no S6/batch/training scope opened.
Trusted accepted-proposal execution verified: runs/20260917T075134Z_s5d_repair_execution.
New USD/physics, hash linkage and official/ITRI gates pass. Stage records 01–05.
128 tests (7 skipped) exit 0: runs/20260917T075203Z_repair_execute_tests.
No genuine model/external geometry execution yet; remain in_progress.
Next exact action: configure model/provider or receive raw model response, submit
through existing guard then run repair-execute without changing acceptance criteria.

Official text-to-carton trial requested: prompt and preflight archived
runs/20260917T083229Z_official_carton_attempt. Service/provider unavailable;
no generation. Next: configure selected provider, query capabilities, submit prompt.
