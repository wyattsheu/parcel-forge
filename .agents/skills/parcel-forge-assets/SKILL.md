---
name: parcel-forge-assets
description: Prepare text-described or image-based robot simulation assets in parcel-forge, execute supported image pipelines, and deliver USD with measured validation and WebRTC instructions.
---
Use the repository CLI; do not reread all source files or historical reports during ordinary operation.

Read AGENTS.md and its required current-state documents. Preserve existing work. Read deeper sources only for the active capability or a failed stage.

- Text: interpret the description into the existing workflow bundle. Keep source/provenance, initial state, free/fixed base, assembly interfaces, physical behaviors and task acceptance explicit. Run `./scripts/pf-workflow text --prompt-file DESCRIPTION --bundle BUNDLE`. This is intake/preflight, not text-model inference. If ready, choose an existing generator only when its actual scope matches. Read `docs/WORKFLOW_CONTRACT.md` for bundle fields; unsupported behavior must stay blocked. Do not approximate movable carton flaps with button/angle animation.
- Image: use an isolated single-object rigid bundle with positive metric length/mass and image attribution. Run `./scripts/pf-workflow image --bundle BUNDLE --image INPUT.png --reference SOURCE --license-note LICENSE` to prepare only. Add `--execute --name EXPORT_NAME` to authorize one TripoSR attempt, USD physical checks, cold load and export. Consult `docs/PORTABLE_SETUP.md` only for setup or another machine.
- Read the returned run's `result.json` and `progress.json` first. Read a stage log and relevant module only when a stage fails; no automatic endless retries or threshold relaxation.
- Deliver measured outcomes, assumptions, limitations, artifact paths, and the WebRTC Script Editor loader. Physics, state readback, rendering, human viewing and real-material calibration are separate. Files existing never prove verification.
- Keep build reports in `reports/development/`, execution evidence under fresh `runs/`, and runtime reports in `reports/runtime/`. Never change shared runtimes/drivers or terminate another session. Check available VRAM before runtime launch.

The image baseline is a whole-object rigid mesh; articulation, wrapping/deformation, shape fidelity and calibrated material properties do not follow from geometry generation.

If a human identifies loose fragments in a single connected rigid asset, use image `--component-policy largest` explicitly after considering legitimate detached parts; default `keep` preserves all parts. Raw mesh and removed components remain in the generation run. Component cleanup does not prove shape correctness; require human review. Image colors are image-derived, not calibrated albedo; authoring uses linearized vertex colors and an explicit PreviewSurface with assumed roughness.
