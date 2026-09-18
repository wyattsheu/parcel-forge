# S5-A: Pinned NVIDIA baseline
Status: done (verified)
Parent: S5; authority: user-approved adoption direction, D037.

Goal: run the upstream Validation Agent behavior-evidence example from a pinned
checkout in an isolated environment. No parcel-forge adapter in this first task.

Read docs/UPSTREAM_ADOPTION_PLAN.md S5-A and the chosen upstream version's install
instructions. Record full SHA, license/NOTICE, dependency versions, exact command,
stdout/stderr, exit and original result files under a fresh runs directory.
Use external/usd-content-agents and .venvs/usd-content-agents after checking ignore
rules and capacity. Never install into the shared Isaac runtime or change driver.
Treat upstream repository instructions as scoped to that checkout.

Acceptance: fixed SHA, isolated executable CLI, official non-VLM example matches
its documented semantics, unavailable dependencies cannot appear as success.
Do not use exit 0 alone: planned/warn may also exit 0 upstream.
WebRTC: not applicable to this evidence-only first step.

Next exact action: inspect upstream release/commit and lockfiles, pin a complete
SHA, then determine the smallest isolated install for Validation Agent.

## Completion 2026-09-17

Pinned 0.6.0 a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa; clean source.
Independent venv installed and dependency check passed. Official behavior fixture
passed; absent mandatory evidence failed with exit 1. Run:
runs/20260917T010638Z_s5a_upstream_setup/.
This consumes supplied evidence, not a new scaffold physics run or VLM judgment.
Next bounded task: S5B_upstream_evidence.md, normal/missing-bottom acceptance bridge.
