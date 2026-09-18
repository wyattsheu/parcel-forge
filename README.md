# parcel-forge

Reproducible asset generation and automated validation for Isaac Sim, built from
zero on 2026-09-16 against the Isaac Sim 6.0.1.0 install already present on this
machine. This repository does not reuse the earlier Task 1 code and never
modifies, reinstalls or upgrades the simulator, the driver or the shared venv.

**Current status:** image→TripoSR→rigid USD→PhysX→cold-load baseline verified; keyboard-carton baseline retained. Text descriptions are captured with a task-specific bundle; general automatic text-to-physical-asset authoring remains partial. See `docs/STATE.md` for measured results.

Start here: [portable setup](docs/PORTABLE_SETUP.md). Common entry: `./scripts/pf-workflow --help`. Codex: `$parcel-forge-assets`; Claude Code: `/parcel-forge-assets`. Both read the same Skill.

New raw runs, venvs, external providers and model weights stay local. Historical evidence already in Git remains in history; exported sample assets and reports are included.

## What actually works today

| capability | status | how it was proven |
| --- | --- | --- |
| Read-only environment inventory + health report | verified | `./scripts/pf doctor` |
| Launch Isaac Sim 6.0.1 headless from this repo | verified | S1 run log under `runs/` |
| Finite-step PhysX simulation (ground + rigid cube) | verified | `trajectory.csv` in the S1 run |
| Per-step pose / orientation / velocity / sim-time read-back | verified | same `trajectory.csv` |
| Offline PNG render of the real final scene | verified | S1 run `renders/scene_final.png` + image statistics |
| WebRTC human viewing of a parcel-forge scene | **not tested** | livestream is never enabled here |
| Five-plate open box built from the handbook geometry | verified | S2 runs; plate sizes read back to 1e-8 m |
| Probe drop judged in the box local frame | verified | S2 suite table: inside / at_mouth / fell_through |
| Two deliberate faults detected (sealed lid, missing bottom) | verified | both fault cases classified correctly, neither passed as `inside` |
| Clean USD asset authored per case | verified | `pf verify`: defaultPrim, SI units, upAxis=Z, 71-line layer |
| Illegal specs rejected before any launch | verified | 7 invalid cases, each with its own error class |
| Static USD checks read back from the output file | verified | 10 G1 rules; dimension error ~1e-8 m |
| NVIDIA generic USD validator (41 registered rules) | verified | runs on every built asset; separate from SimReady and Isaac-specific physics rules |
| Proof that the official validator can fail | verified | `G7`: 3 failures on a deliberately broken fixture |
| Closed-form box mass/COM/inertia maths | verified | rotated impossible and small-valid counterexamples are permanent regressions |
| Dynamic USD mass/COM/inertia authoring | verified | static USD readback plus PhysX tensor-view readback |
| Nine-point placement | verified | 9/9 inside; trajectory, scene and PNG evidence |
| Four-direction side-wall physics | verified | 4/4 blocked from full trajectories; original optional render crashed separately |
| Dynamic-box settling, batch driver, repair loop, VLM review | **not implemented** | planned for remaining S4-S7 |

Nothing above is claimed from reading code. Each "verified" row points at a run
directory containing the command, exit code, log and outputs.

## Requirements

Nothing to install. `scripts/pf` runs on the system Python 3 with the standard
library only, and re-launches itself inside the existing Isaac runtime for
anything that needs Kit. Paths live in `config/isaac_env.json`.

## Usage

```bash
./scripts/pf doctor            # read-only environment health -> runs/<id>/doctor.json
./scripts/pf smoke             # S1 cube drop -> runs/<id>/{trajectory.csv,renders/,summary.md}
./scripts/pf smoke --device 1  # pick a different GPU
./scripts/pf box --case open_box_normal   # one S2 case -> runs/<id>/
./scripts/pf box --all                    # all six legal cases + a suite table (GPU)
./scripts/pf verify --all                 # 13 cases: schema -> USD -> static checks (~4 s, no GPU)
./scripts/pf build --case open_box_small  # schema check, then author asset.usda
./scripts/pf mass-readback                 # dynamic USD -> PhysX mass/COM/inertia readback
./scripts/pf placement-grid --physics-only # nine placements, rendering separately optional
./scripts/pf sidewall --physics-only       # four-direction wall impact
./scripts/pf dynamic-drop                  # dynamic rigid box settling
./scripts/pf view --run <id> --scene scene_final.usda --ui
./scripts/pf runs --last 5     # list recent runs with stage and exit code
```

Subcommands from the handbook that are **not implemented yet**
(`simulate`, `render`, `batch`) exist in the CLI
only to exit 4 and say so, rather than to pretend.

### Exit codes

| code | meaning |
| --- | --- |
| 0 | all required checks actually ran and passed |
| 2 | asset or specification failure |
| 3 | environment or tooling failure |
| 4 | insufficient evidence (including "not implemented yet") |

Raw exit codes from the Isaac runtime are stored separately in each run's
`manifest.json` as `external_exit_code` and are never conflated with these.

## How to read the results

Every run lands in its own `runs/<timestamp>_<kind>/` directory and is never
overwritten:

```
manifest.json     code commit + dirty-diff hash, profile hash, command, exit codes, device, dt
environment.json  measured host/GPU/Isaac inventory at run time
profile.json      the acceptance thresholds this run was judged against
trajectory.csv    per-step sim_time, position, quaternion (w,x,y,z), linear and angular velocity
s1_result.json    per-check verdicts with the numbers behind them
renders/          PNG evidence plus the camera pose that produced it
logs/             the full Isaac runtime log, including the exact command
summary.md        human-readable capability table and check table
```

`summary.md` reports physics execution, state read-back, headless operation,
offline rendering and WebRTC human viewing **separately**. An agent never claims
to have looked at an image; it reports the image's measured statistics and path.

## Repository layout

```
scripts/pf                      CLI entry point (system Python, stdlib only)
src/parcel_forge/envprobe.py    read-only host/GPU/Isaac inventory
src/parcel_forge/doctor.py      environment health report
src/parcel_forge/evidence.py    run directories, manifests, hashing
src/parcel_forge/pngio.py       stdlib PNG encoder + blank-frame statistics
src/parcel_forge/runtime/       launcher (host side) + Isaac Sim 6.0 adapter (in-runtime)
src/parcel_forge/smoke_s1.py    S1 scene, stepping, checks (runs inside Isaac)
src/parcel_forge/smoke_host.py  S1 host driver: run dir, launch, manifest, summary
src/parcel_forge/geometry.py    open-box plate table and spec rejection (pure maths)
src/parcel_forge/validation/    outcome classification, internal G1 rules, official NVIDIA validator
src/parcel_forge/box_s2.py      S2 box + probe scene and checks (runs inside Isaac)
src/parcel_forge/box_host.py    S2 host driver: per-case runs and the suite table
src/parcel_forge/schema.py      case-file validation with named error classes (stdlib)
src/parcel_forge/usd_author.py  writes the open-box asset as a clean USD layer
src/parcel_forge/usd_tool.py    in-runtime build/validate entry point (pxr only, no Kit)
src/parcel_forge/build_host.py  S3 host driver: schema first, then build and validate
profiles/                       versioned acceptance thresholds
docs/                           STATE, ROADMAP, ENVIRONMENT, DECISIONS, METHODS, tasks/, sessions/
runs/                           append-only evidence
cases/                          legal cases, including deliberate geometry faults
cases/invalid/                  specs that must be rejected, plus their expected error classes
tests/                          offline regressions: geometry, outcome rule, PNG
```

## Rules for anyone (human or agent) working here

See `AGENTS.md`. The short version: read the handoff files before changing
anything, write evidence before summarising it, never relax a threshold or
disable a collider to make something pass, never stop another user's process,
and never report an untested capability as passing.

逐項自行驗證與 WebRTC 指令：[從零到現在清單](reports/development/2026-09-17_self_verification_from_zero.md)。
人工確認紀錄：[空白確認表](reports/execution/2026-09-17_human_self_check.md)。

NVIDIA 0.6.0 原廠驗證基準已跑通：[S5-A 重跑指令與結果](reports/development/2026-09-17_s5a_upstream_baseline.md)。
後續錄製需求見 [採用計畫](docs/UPSTREAM_ADOPTION_PLAN.md)，MP4 實作在 S5-C。

實測軌跡影片與重跑／WebRTC 開啟方式：[S5-C 錄製影片](reports/development/2026-09-17_s5c_recorded_video.md)。

影片可按需在背景產生：`./scripts/pf-video-background --run <S2-run-id>`；[指令與修復工具進度](reports/development/2026-09-17_s5d_guard_and_background_video.md)。


## Four-flap carton rigid-hinge proxy (2026-09-17)

[建置成果、來源與WebRTC回放](reports/development/2026-09-17_carton_proxy_milestone.md) ·
[實際執行進度](reports/execution/2026-09-17_carton_proxy_runs.md)。

```bash
./scripts/pf-carton --physics-device cpu --scenario opening-order --crease-friction-nm 0.005
```

Four flaps open/recover with a Python viscoplastic controller; explicit .005Nm friction effort uses Isaac6 API.
See opening_diagnostic_status (legacy mixed-load gate retained, host exit1 intentional).
recording.usda is measured playback; asset.usda is passive unless the controller runs.
Material parameters estimated; orthotropic panel bending/real calibration/IsaacLab integration not verified.

## 圖片生成剛體基線

真實電鑽照片已經TripoSR生成OBJ/GLB並通過Isaac6.0.1剛體/冷載入。交付exports/image_drill_v1；[來源、限制與WebRTC指令](reports/development/2026-09-18_image_drill_delivery.md)。尺寸質量為假設；人工外形/接觸保真未確認，沒有宣稱完整物理材料重建。
