# Project contract

Build a reproducible Isaac Sim asset generation and validation workflow.
Current scope: primitive open boxes and rigid probes on the PhysX baseline of the
**already-installed** Isaac Sim. This repository was started from zero on
2026-09-16 and deliberately does not reuse the older Task 1 code.

## Every session starts here

1. Read `docs/STATE.md`, `docs/ROADMAP.md`, `docs/ENVIRONMENT.md`, the current
   task card in `docs/tasks/`, and the newest file in `docs/sessions/`.
2. Run `git status`. Preserve any pre-existing changes; never discard work you
   did not create.
3. Re-run the smallest relevant benchmark (today: `./scripts/pf smoke`) before
   claiming the previous state still holds.
4. Summarize milestone, evidence and the single next action in Traditional Chinese.
5. Treat the version-matched local install as the API reference. This machine runs
   Isaac Sim 6.0.1.0, where `isaacsim.core.api` no longer exists; read
   `site-packages/isaacsim` rather than trusting 4.x tutorials or memory.

## Every session ends here

1. Write tool output into a fresh `runs/<run-id>/` directory **before** summarizing it.
2. Update `docs/STATE.md` (latest summary only) and the current task card.
3. Append `docs/sessions/<timestamp>.md` with commands, exit codes, run paths,
   what passed, what is blocked, and one exact next action.
4. Record significant technical choices in `docs/DECISIONS.md` as a new D-number;
   never delete a superseded reason.

## Environment rules (non-negotiable)

- Never reinstall, upgrade or reconfigure Isaac Sim, the driver, or the shared venv.
- Never install packages into the Isaac runtime. Prefer the Python standard library.
- Never stop, kill or reset another process, session or shared environment.
  The user's WebRTC viewer owns ports 49100/47998; parcel-forge always runs with
  livestream disabled.
- Check free VRAM before launching. If resources are missing, write a `blocked.json`
  with the reason and stop; do not free resources by force.
- Never print secrets, API keys or whole environment dumps.

## Evidence rules (non-negotiable)

- A file that exists is "implemented", not "verified". Verified means a command
  ran, exited, and its output is saved under `runs/`.
- Report physics execution, state read-back, headless operation, offline rendering
  and WebRTC human viewing **separately**. One of them passing proves nothing
  about the others.
- Anything not measured is `not_tested` or `unknown`, never `pass`.
- An agent may never claim to have looked at an image. It may only report the
  image's measured statistics and its path. Only a human confirms a WebRTC view.
- A flat or black frame is a render failure, recorded separately from physics success.
- Never repair an asset by relaxing a threshold, editing an acceptance profile,
  disabling collision, or fixing the validator. Fix the spec or the generator.
- Never upgrade the simulator or a dependency as an incidental repair.
- Keep estimated physical parameters marked as estimates (`provenance` fields).
- Run directories are append-only. A new attempt gets a new id; old evidence stays.

## Execution rules

- One bounded task card at a time; finish it before widening scope.
- Keep specification, asset generation, validation and agent repair in separate modules.
- Do not add services, databases, MCP, ROS, Isaac Lab or training pipelines
  unless the current stage's task card requires them.
- Do not publish, push or share this repository automatically.
- When teaching the user, give one concept plus one experiment that changes a
  single parameter.
