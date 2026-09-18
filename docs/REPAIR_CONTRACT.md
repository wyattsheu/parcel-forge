# S5-D repair contract, version 2

Active schema: contracts/repair_proposal_v2.schema.json.
Runtime gate: src/parcel_forge/repair_guard.py. Structural validation uses Python
standard library checks; independent JSON Schema parity checks run in the isolated
upstream environment. Both must reject protected fields. Version 1 is deprecated:
its former conflicting structures are rejected, not silently migrated. The former
permissive schema is retained in integration evidence and D044's reason.

An outer actor submits only JSON, never a verdict. Required fields: schema,
source_run, source_spec_sha256, attempt, changes. Exactly one change is allowed:
/geometry/fault from sealed_lid or missing_bottom to none. Probe, intended_task,
expected_outcome, provenance, dimensions, material and all other fields stay fixed.
No profiles, acceptance thresholds, validator, generator or evidence edits.

The trusted CLI reads only a real local source run and a proposal in
contracts/repair_proposals/ or runs/, rejecting symlink inputs and path escapes.
It freezes the six source evidence files and verifies their hashes and measured
state with the existing gate. It preserves source.json and candidate.json unchanged
apart from the allowed fault removal; source binding lives in proposal_result.json
rather than extra fields that would break the case schema.

A controller-owned flock serializes attempt reservation. Fresh append-only
attempt_receipt.json files count each submission, including rejected proposals;
maximum three per original source run. Actor attempt must match the actual next
receipt. Reusing attempt=1 does not reset the budget. Reservation requires valid
source evidence and allowed input paths. v1 historical proposals without receipts
are not retroactively counted; v2 starts the enforced budget. A failed reservation
or fourth submission emits a rejected result, never a candidate. No actor may edit
receipts or launch unlimited new source simulations to evade the controller budget.

`pf repair-link-check` verifies source snapshot -> proposal -> candidate ->
validation request byte hashes, candidate recomputation, unchanged profile and
measured task outcome. It establishes content linkage only; matching a historical
validation run does not establish a new simulation or temporal execution order.
Application success and hash linkage are not physical repair success. A new live
repair requires a new physics run and passing task gate, separately reported.

The proposal gate is not an actor filesystem sandbox. Landlock probes currently
cover content-write operations; complete read/network/process/metadata/FD isolation
is pending. No untrusted model shell is authorized by merely passing this gate.

Pinned NVIDIA 0.6.0 provides focused validation/checkpoints, not a general custom
spec-repair plug-in or fifth validation template. Keep ITRI spec repair and required
task gates external; do not claim NVIDIA's USD topology/physics repair modifies our
box spec. See reports/development/handoffs/upstream_wiring_audit.md.

Self-check (proposal attempt must reflect the controller budget):

```bash
./scripts/pf repair-proposal --source-run <original-run-id> --proposal <v2-proposal.json>
./scripts/pf repair-link-check --proposal-run <proposal-run-id> --validation-run <measured-run-id>
```

Do not repeatedly run a bound attempt=1 fixture against the same live source;
rejection still consumes a reserved submission. Offline budget tests use isolated
fixtures. Background videos remain on demand, outside numerical acceptance.
