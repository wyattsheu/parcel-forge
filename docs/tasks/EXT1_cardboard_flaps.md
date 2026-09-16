# Task EXT1: RSC flaps and crease mechanics
Status: todo (extension, not part of S0-S7)
Depends on: S4 verified, and D017 (dt-dependent containment) resolved

Background and sources: `docs/research/CARDBOARD_MECHANICS.md`.
Handbook section 17 places flaps, cups and packaging materials after the rigid
baseline. This card exists so the requirement is recorded, not so it jumps the queue.

## Goal
The box becomes a Regular Slotted Container with four flaps that fold at crease
lines, resist until a threshold, and stay folded once creased.

## Stage A - geometry only (pure maths, no physics)
Extend `geometry.py` with the RSC flap table. The defining rule is exact and
testable offline:

- all four flaps have the same length
- `flap_length = W / 2`, so the two outer flaps meet at the centre line
- flaps exist at both the top and the bottom opening
- reject specs where a flap would be longer than the face it folds against

Acceptance: unit tests pin `flap_length == W/2` and that the two outer flaps meet
with zero gap at the centre for the demo box (W = 0.20 -> each flap 0.10 m).
No simulator involved, same as `tests/test_geometry.py` today.

## Stage B - flaps as articulated rigid bodies
Each flap becomes a child rigid body joined to its wall by a **revolute joint** on
the crease line. Exactly one articulation root; flaps are links, never free bodies.

- joint limits: the physical fold range (roughly 0 to 180 degrees)
- joint drive: stiffness and damping give the restoring torque -- the resistance
  before the board gives
- all values start as `uncalibrated_assumption` in provenance

Acceptance: flaps hold their pose under gravity; a commanded fold reaches the
target; nothing separates from the articulation root; the existing S2 containment
cases still pass unchanged with flaps open.

## Stage C - the crease yield rule
PhysX joints are elastic, so permanent creasing must be explicit:

1. monitor joint torque
2. when it exceeds `crease_yield_torque_nm`, move the drive rest angle toward the
   current angle and reduce drive stiffness by `crease_softening_factor`
3. record every yield event in the run evidence with the torque that caused it

This encodes the documented fact that a crease is permanently weaker than the
surrounding board, and that folds are the most common box failure site.

Acceptance: a flap pushed below the threshold springs back; pushed above it, it
stays folded and is measurably easier to fold the second time. Both directions are
separate test cases -- a model that only ever yields is as wrong as one that never does.

## Explicitly out of scope
- Deformable/FEM board. Isaac Sim's deformables are currently passive and cannot be
  attached to rigid articulations, so a robot could not grip a deformable flap.
- Claiming ECT or BCT numbers. Those describe crushing, not folding, and we cannot
  crush anything yet. The McKee formula is recorded in the research note as a future
  validation target, not as a simulation input.

## User learning
Concept: a crease is not a hinge. A hinge returns; a crease gives way at a threshold
and is permanently weaker afterwards. That asymmetry is the whole behaviour, and it
is a rule we write, not something the physics engine provides.
Experiment: with Stage C running, fold one flap just under the yield torque and one
just over, then try to fold both again and compare the torque needed.

## Next action
Stage A only: add the flap table to `geometry.py` with unit tests proving
`flap_length == W/2` and that the outer flaps meet at the centre. Do not touch the
simulator in the first sitting.
