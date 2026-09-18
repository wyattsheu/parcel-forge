# S5-B: ITRI evidence bridge into upstream validation
Status: done (verified)
Depends on: S5-A verified. Authority: D037 and UPSTREAM_ADOPTION_PLAN.md.

Read pinned upstream ValidationRequest and physical_behavior inputs before coding.
First reuse normal runs/20260917T000053Z_s2_open_box_normal/ and missing-bottom
runs/20260917T000039Z_s2_open_box_no_bottom/. Run physics_sane on available USD;
bridge task measurements through a supported contract or separate required ITRI gate.
Never invent a supported evidence type or synthesize model approval.

Keep simulation_execution, task_acceptance and regression_expectation distinct.
Missing-bottom regression pass means fault detection works, NOT inside-task pass.
Normal task passes, missing-bottom task fails, missing/tampered data cannot pass.
Then execute two fresh physics cases and confirm the bridge isn't hardcoded to old IDs.
Required output: original upstream reports + ITRI findings + source hashes + exact
commands/exit in fresh runs and both report folders. No acceptance-profile changes.
Record rendering and human viewing separately. Video at S5-C uses exact measured
rollout, preserves frames and adds an MP4 for convenient review, not as judge input.

Next exact action: inspect upstream behavior evidence schema and plan minimal
normal/missing-bottom mapping without converting regression verdict to asset verdict.

## Completion

Old and fresh normal/missing-bottom checks verified; independent task gate retained
without synthetic upstream approval. 111 tests, 7 skipped. Suite: runs/20260917T012612Z_s5b_completion/bridge_suite.json.
Next: S5C_recorded_video.md.
