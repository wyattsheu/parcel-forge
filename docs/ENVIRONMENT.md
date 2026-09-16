# Environment

Everything here was measured read-only on the machine on 2026-09-16 (UTC).
Nothing was installed, upgraded, started or stopped to produce it.
Machine-readable copies: `config/isaac_env.json` and any run's `environment.json`.

## Host

| item | value |
| --- | --- |
| user@host | wyattsheu@acm-803-1 |
| OS | Ubuntu 24.04.3 LTS, kernel 6.14.0-37-generic |
| system python | 3.12.3 (`/usr/bin/python3`) — runs `scripts/pf` itself |
| project path | `/mnt/HDD4/wyattsheu/ITRI/parcel-forge` |
| NVIDIA driver | 580.126.09 (CUDA 13.0 runtime reported by nvidia-smi) |
| GPU 0 / GPU 1 | 2x NVIDIA RTX PRO 6000 Blackwell Max-Q, 97887 MiB each |

## Isaac Sim (pre-existing, must not be modified)

| item | value |
| --- | --- |
| install kind | pip packages inside a uv-managed venv |
| interpreter | `/mnt/HDD4/wyattsheu/IsaacLab/.venv/bin/python3` (Python 3.12.14) |
| working directory used at launch | `/mnt/HDD4/wyattsheu/IsaacLab` |
| isaacsim | 6.0.1.0 (`VERSION` file: `6.0.1-rc.7+release.42383.32955d8d.gl`) |
| isaacsim-kernel / -core / -app | 6.0.1.0 |
| isaaclab | 16.4.0 — present, deliberately unused (see D001) |
| torch / numpy / warp-lang | 2.11.0+cu128 / 2.5.1 / 1.16.0 |
| pydantic | 2.14.0a1 — present, unused at this stage |
| usd-core wheel | absent; `pxr` is provided inside the Isaac runtime itself |

### API shape on this version

Isaac Sim 6.0 does **not** ship `isaacsim.core.api` (the 4.x `World`,
`DynamicCuboid`, `SimulationContext`). What exists here:

- `isaacsim.SimulationApp` — standalone launcher, constructed before any Kit import.
- `isaacsim.core.simulation_manager.SimulationManager` — `setup_simulation(dt, device)`,
  `step(steps=...)`, `get_simulation_time()`, `get_physics_dt()`, `get_device()`.
- `isaacsim.core.experimental.prims.RigidPrim` — `get_world_poses()` (quaternion
  returned as **w, x, y, z**), `get_velocities()`, `get_masses()`, `get_inertias()`.
- `isaacsim.core.experimental.objects`, `omni.replicator.core`, `pxr`, `omni.timeline`.

## Launch method used by parcel-forge

`scripts/pf smoke` re-executes an in-runtime script through
`src/parcel_forge/runtime/launcher.py`, reproducing the environment that the
machine's known-good WebRTC launcher uses, **minus livestream**:

```
cwd=/mnt/HDD4/wyattsheu/IsaacLab
OMNI_KIT_ACCEPT_EULA=Y OMP_NUM_THREADS=4
ISAAC_LAB_ENABLE_ISAAC_RTX_PER_ENV_SCENE_PARTITION=0
CUDA_VISIBLE_DEVICES=0
LD_PRELOAD=<venv>/nvidia/cuda_runtime/lib/libcudart.so.12
<venv>/bin/python3 src/parcel_forge/smoke_s1.py --out runs/<id> --profile runs/<id>/profile.json
```

Startup cost measured: Kit ready in roughly 13-27 s.

## Pre-existing sessions on this machine (left alone)

- A user WebRTC USD viewer: `view_usd_webrtc.py` under
  `/mnt/HDD4/wyattsheu/handoff/robot129_pro6000_sim_20260913/`, launched through
  `tools/start_usd_webrtc.sh`, holding **signaling port 49100** and stream port 47998,
  and using GPU 0. parcel-forge never enables livestream and never touches those ports.
- A second unrelated compute process occupying tens of GiB on GPU 1.

Neither was stopped, inspected for secrets, or modified. parcel-forge selects
`CUDA_VISIBLE_DEVICES=0` by default because GPU 0 had ~91 GiB free while GPU 1 was
at 97% utilisation; override with `./scripts/pf smoke --device 1`.

## Known unknowns (do not report as working)

- WebRTC viewing of a parcel-forge scene: never attempted. Only a human can confirm it.
- Isaac Sim's official asset-validation rule set: not yet invoked (S3).
- Determinism across GPUs/drivers: not measured.
- Any Isaac Lab, MCP, ROS, Blender or VLM capability: not installed or not tested.
