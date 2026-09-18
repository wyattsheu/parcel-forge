# S5-C: Exact rollout recordings and clickable MP4
Status: done (verified); limited to measured single-probe S2 recordings
Depends on: S5-B verified.

Capture/export measured position and quaternion of every relevant rigid body with
original time/dt/seed. Begin with normal and missing-bottom source trajectories.
Retain source hashes and freeze evidence. Export self-contained time-sampled USD;
check its samples against CSV. Do not rerun physics to manufacture recorded motion.
Prefer pinned upstream playback/render; use thin local adapter only where necessary.
Create PNG frames, encode H.264 MP4 with existing ffmpeg, save fps/playback-speed,
encoder version/command, frame statistics, ffprobe frame/duration and hashes.
Rendering and physics have separate statuses. Only a human confirms visual content.
Pure recording playback must disable physics so simulation cannot replace samples.

Acceptance: both measured recordings verified, nonblank motion-containing frames,
playable MP4 with provenance and direct links in both report types. No claim that
MP4 is accepted by an upstream PNG-only judge. No model calls are needed here.
Next exact action: proceed to S5D_bounded_upstream_repair.md and inspect official request/checkpoint hooks.

Evidence: runs/20260917T015400Z_s5c_completion/suite.json. Both video commands exit 0; 900 samples each exact. Human viewing not_tested. See reports/development/2026-09-17_s5c_recorded_video.md for limitations and sources.
