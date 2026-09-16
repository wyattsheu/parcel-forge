# parcel-forge

Reproducible asset generation and automated validation for Isaac Sim, built from
zero on 2026-09-16 against the Isaac Sim 6.0.1.0 install already present on this
machine. This repository does not reuse the earlier Task 1 code and never
modifies, reinstalls or upgrades the simulator, the driver or the shared venv.

**Current stage: S1 complete. S2 (open box) not started.**
Read `docs/STATE.md` for the verified state and the single next action, and
`docs/ROADMAP.md` for the S0-S7 plan.

## What actually works today

| capability | status | how it was proven |
| --- | --- | --- |
| Read-only environment inventory + health report | verified | `./scripts/pf doctor` |
| Launch Isaac Sim 6.0.1 headless from this repo | verified | S1 run log under `runs/` |
| Finite-step PhysX simulation (ground + rigid cube) | verified | `trajectory.csv` in the S1 run |
| Per-step pose / orientation / velocity / sim-time read-back | verified | same `trajectory.csv` |
| Offline PNG render of the real final scene | see `docs/STATE.md` | S1 run `renders/` + image statistics |
| WebRTC human viewing of a parcel-forge scene | **not tested** | livestream is never enabled here |
| Open-box geometry, USD authoring, schema, batch, repair loop | **not implemented** | planned for S2-S7 |

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
./scripts/pf runs --last 5     # list recent runs with stage and exit code
```

Subcommands from the handbook that are **not implemented yet**
(`build`, `validate`, `simulate`, `render`, `verify`, `batch`) exist in the CLI
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
profiles/                       versioned acceptance thresholds
docs/                           STATE, ROADMAP, ENVIRONMENT, DECISIONS, tasks/, sessions/
runs/                           append-only evidence
cases/ tests/ src/.../validation/   empty until S2/S3
```

## Rules for anyone (human or agent) working here

See `AGENTS.md`. The short version: read the handoff files before changing
anything, write evidence before summarising it, never relax a threshold or
disable a collider to make something pass, never stop another user's process,
and never report an untested capability as passing.
