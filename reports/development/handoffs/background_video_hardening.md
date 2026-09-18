# Sub-task handoff: background_video_hardening

Scope granted by main AI: harden `scripts/pf-video-background` only
(worker exception handling, simple status query, duplicate-start handling,
job-directory name collision handling). On-demand execution only, no daemon
or scheduler, no change to `video_host`'s acceptance conditions, no GPU/model
launch. This report separates implementation, offline/fake-process testing,
and (not performed) physical execution / rendering / human viewing, per
AGENTS.md evidence rules.

## Baseline

- Base commit: `f4e5586c4a42e75aee146c5729f68718f4ba58ae`
  ("Record D027: the probe weighs 0.49 N, which is why drag throws it").
- Workspace had pre-existing uncommitted changes at task start (many modified
  and untracked files from the main AI's S5 work); none were touched, reset,
  or discarded. `git status --porcelain -- scripts/pf-video-background`
  showed the file as untracked (`??`) before and after this task — it was
  added in an earlier uncommitted session and has no prior git history, so
  there is no line-level diff against a previous committed version; the
  whole current file content is the delta from "did not exist in git".

## Files read

- `AGENTS.md`, `docs/STATE.md`, `docs/ROADMAP.md`, `docs/ENVIRONMENT.md`,
  `docs/tasks/S5D_bounded_upstream_repair.md`,
  `docs/sessions/20260917T020054Z.md` (newest session),
  `docs/UPSTREAM_ADOPTION_PLAN.md` (skimmed for scope confirmation only).
- `src/parcel_forge/video_host.py` (read-only, to confirm where the real
  acceptance logic — `video_result.json` / `test_recording.mp4` — lives, so
  it would not be touched).
- `runs/20260917T020054Z_background_video_verified/verification.json` (prior
  evidence of the unhardened script's happy path).

## File modified

- `scripts/pf-video-background` — the only file changed. Nothing else in
  the repository was touched (no profiles, tests, STATE/ROADMAP/DECISIONS,
  video_host.py, or shared runtime code).

## What changed, with source anchors (all in `scripts/pf-video-background`)

1. **Worker exceptions no longer strand a job.** `worker()` (line 39) now
   wraps request parsing, subprocess execution, and evidence parsing in
   `try/except Exception` (lines 44–66); any internal failure (malformed
   `job_request.json`, unreadable log, malformed `video_result.json`, etc.)
   still writes `job_result.json` with `status: "failed"` and an `error`
   field (line 68), instead of leaving the job directory with no completion
   signal. The previous version had no such guard and would raise past the
   `write(job/'job_result.json', ...)` call on any of these failures.
2. **Simple status query.** New `--status JOB` flag (line 187, wired at
   line 189) resolves a job by directory name under `runs/` or by absolute
   path (`resolve_job_arg`, line 137) and reports one of `completed`,
   `running`, `stalled`, or `unknown` (`status_of`, line 109), using
   `pid_alive` (line 29, `os.kill(pid, 0)`) to distinguish a worker that is
   still alive with no result yet (`running`) from one whose process is gone
   with no `job_result.json` (`stalled` — e.g. the wrapper process itself
   was killed before `worker()` could run). A job dir with a corrupt
   `job_request.json` reports `state: "unknown"` with the parse error
   instead of crashing the CLI.
3. **Duplicate-start handling.** `find_active_job()` (line 71) scans
   `runs/*_background_video` job dirs, matches `job_request.json`'s
   `source_run` against the requested `--run`, and treats a job as active
   only if it has no `job_result.json` yet **and** its recorded pid is still
   alive. `cmd_start()` (line 151) refuses to launch a second job for the
   same source run while one is active (prints the existing job's status,
   exits 3) and allows a new one again once the prior job has completed.
4. **Job-directory name collisions.** `make_job_dir()` (line 95) replaces
   the old bare `job.mkdir()` (which raised uncaught `FileExistsError` if
   two jobs started in the same UTC second) with a retry loop that appends
   `-1`, `-2`, … to the timestamp-based name until an unused directory is
   created.
5. Added a module-level `if __name__ == '__main__':` guard (line 201) around
   all CLI entry logic so the file can be imported (e.g. for testing) without
   side effects — the previous version executed `argparse` parsing at import
   time unconditionally.

No change to: the `pf video` command line invoked (`[pf, video, --run, ...]`),
the shape of `job_request.json`'s `command` field, `video_host.py`, any
profile, or any acceptance threshold.

## Testing performed (offline, controlled fake processes — no real render)

All tests ran against an isolated sandbox copy of the script under this
session's scratchpad (`/tmp/.../scratchpad/bgvideo_test/`), with its own
`scripts/pf-video-background` and a **fake** `scripts/pf` stand-in that only
manages files/processes (never launches Isaac Sim, GPU code, or a real
renderer) and writes `FAKE-NOT-A-REAL-VIDEO` as its "video" bytes so its
output cannot be mistaken for a real render result. This keeps synthetic
evidence out of the real repository `runs/` tree.

Commands and exit codes:

1. Normal path: `pf-video-background --run fake_source_run` → launch exit 0;
   worker completed with `job_result.json` `status: "pass"`;
   `--status <job>` → exit 0, `state: "completed"`.
2. Fake-`pf` exits non-zero (simulated internal `raise` inside the fake
   render step, `FAKE_BEHAVIOR.txt` = `crash`): launch exit 0; worker still
   exits 1 and writes `job_result.json` with `status: "failed"`,
   `exit_code: 1`. Confirms ordinary non-zero subprocess exits were already,
   and remain, captured.
3. **Internal worker exception** (direct `--worker JOB` call against a job
   dir with a corrupted `job_request.json`, i.e. not valid JSON): worker
   exit 1; `job_result.json` written with `status: "failed"`,
   `exit_code: null`, `error: "JSONDecodeError: Expecting value: line 1
   column 1 (char 0)"`. This is the case the original script could not
   handle — it would have raised out of `worker()` with no result file.
   `--status` on the same corrupted job dir → exit 1, `state: "unknown"`,
   parse error surfaced instead of a traceback.
4. **Duplicate start**: launched a job against a slow fake `pf`
   (`FAKE_BEHAVIOR.txt` = `slow`, 5 s sleep); a second `--run` for the same
   source while the first was still alive → exit 3, "already active"
   message with the existing job's status; after the first job completed, a
   third launch for the same source succeeded (exit 0).
5. **Job-directory collision**: called `make_job_dir()` directly three times
   with `datetime.now` monkey-patched to a fixed instant → produced
   `..._background_video`, `..._background_video-1`, `..._background_video-2`,
   all created successfully, no `FileExistsError`.

Evidence: transcript of these five runs (commands, stdout, and the printed
`job_result.json`/status JSON) is in this conversation's tool output; per
task scope ("offline/controlled fake test only, no real video/GPU"), no
`runs/` evidence directory was created in the real repository for this
sub-task, since doing so would need real trajectory-run evidence and would
mix synthetic process-management fixtures into the append-only evidence
tree. If the main AI wants a permanent `runs/<id>_background_video_hardening/`
record, say so and it can be produced by replaying test 1–5 verbatim against
the real `scripts/pf` and a real existing local recorded-trajectory run
under `runs/`.

Sanity check against the real script (not the sandbox): `python3 -c
"import ast; ast.parse(open('scripts/pf-video-background').read())"` → parses
cleanly (`OK_SYNTAX`).

## Explicitly not tested / not done

- No real invocation of `scripts/pf video` or `scripts/pf-video-background`
  against real repository `runs/` data — no physical execution, no
  rendering, no GPU use, no human/WebRTC viewing, per sub-task authorization.
- No unit tests were added to `tests/` (out of granted scope — that tree
  belongs to the main AI's S5-D work; this task's tests were run
  offline/out-of-repo as instructed).
- Did not verify behavior when the wrapper `Popen` process itself is killed
  before `worker()` starts (this correctly surfaces as `state: "stalled"` in
  `--status`, but that specific kill scenario was reasoned through, not
  exercised, since it requires sending a real signal to a live process this
  session would then have to manage).

## Blockers / open interface questions for the main AI

- None. No shared file, profile, threshold, or other AI's file was touched.
- One judgment call worth flagging: duplicate-start protection refuses a
  second launch (exit code 3) rather than silently reusing the existing job
  or queuing. If the main AI's S5-D flow expects "start" to always be
  idempotent and return the existing job's info with exit 0 instead of
  refusing, that's a one-line change in `cmd_start()` (line 151) — flagging
  now rather than silently picking a policy for a shared entry point.

## Suggested next step for the main AI

Merge `scripts/pf-video-background` as-is (it is a new, currently untracked
file with no other consumers found in `src/` or `tests/`), then, if S5-D's
integration wants durable evidence, run one real `--run <existing-trajectory-run>`
job against it and save the resulting `job_result.json`/`video.log` under a
new `runs/<id>_background_video/` per the project's append-only evidence
rule — that step is physical execution and is intentionally left to the main
AI's integration pass, not performed here.
