# Corrugated board: what a real box does, and what we can actually simulate

Written 2026-09-16 after the user pointed out that our box "doesn't look like a
cardboard box" -- no flaps, no crease lines, and none of the characteristic
behaviour where the board resists until a threshold and then folds and stays folded.

This document separates three things that are easy to blur: **what real board does**,
**what the simulator can represent**, and **what we are choosing to build**. Numbers
below come from the cited sources; none are measurements of any specific box, and
none may be entered into a case file without a `provenance` tag saying so.

---

## 1. What a real corrugated box is

A corrugated box is not a solid-walled tub. It is one flat sheet of **corrugated
fiberboard** -- a sandwich of flat liners bonded to a wavy fluting -- that is
**scored** (indented along fold lines) and **slotted**, then folded into shape.
Our current asset models the folded result as five solid plates, which is a fair
rigid stand-in for the *body* but has no flaps and no fold lines at all.

### Geometry: the Regular Slotted Container (RSC)

The RSC is the standard shipping box. Its defining rule is simple and directly
implementable:

- All four flaps are the **same length**.
- The outer flaps are **half the box width**, so the two of them meet exactly at
  the centre line when closed.

That gives `flap_length = W / 2` for a top-opening RSC, on both the top and the
bottom. Minimum practical size is about 3 x 3 x 3 inches, and length is
conventionally >= width. Flute direction is usually perpendicular to the sheet
length for top-opening RSCs.

Sources: [Packsize on RSC variants](https://www.packsize.com/blog/7-variants-on-the-regular-slotted-container-box),
[Fantastapack RSC](https://www.fantastapack.com/products/regular-slotted-container-rsc),
[Nature-Pack glossary](https://www.nature-pack.com/glossary/regular-slotted-container-rsc/).

### The crease line is the interesting part, and it is the weak part

A crease (score) is a deliberate indentation that lets the board fold neatly.
The literature is blunt about the consequence: **the most common failure site in a
corrugated box is at the folds**, because the creasing operation itself reduces
stiffness there. Crease depth matters at the scale of microns -- imperfections of a
few microns produce measurable drops in bending stiffness. Which way the board is
bent also matters: bending so the lower-wave-side layers are compressed gives
roughly **10% higher** stiffness than the other direction.

So the user's intuition is right and is worth stating precisely: a crease is not a
free hinge. It is a hinge that **resists, then yields, then stays yielded** -- and
it is permanently weaker afterwards.

Sources: [Influence of Analog and Digital Crease Lines on Mechanical Parameters of Corrugated Board and Packaging (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9268991/),
[Analytical Determination of the Bending Stiffness of a Five-Layer Corrugated Cardboard with Imperfections](https://doi.org/10.3390/ma15020663),
[Effect of Scoring Condition on Creasing Characteristics of Double-Wall Corrugated Board](https://www.researchgate.net/publication/258658393_Effect_of_Scoring_Condition_on_Creasing_Characteristics_of_Double-Wall_Corrugated_Board).

### The standard strength numbers, and what they are good for

Two industry measurements matter, and neither is a material constant you can paste
into a physics engine:

- **ECT (Edge Crush Test)**: cross-direction crushing resistance of the board, in
  kN/m. It predicts stacking strength, not folding behaviour.
- **BCT (Box Compression Test)**: top-to-bottom strength of the finished box.

They are linked by the **McKee formula** (1963), in metric form:

```
BCT = 5.874 * ECT * CAL^0.508 * PER^0.492
      ECT in kN/m, CAL (caliper/thickness) in mm, PER (box perimeter) in cm
```

The simplified McKee form is reliable only for single-wall RSCs with height at
least perimeter/7 and a footprint ratio no worse than 3:1. Crucially for us,
**flap crease placement changes BCT** -- there is published work specifically on
boxes with shifted creases on the flaps.

Sources: [Edge crush test (Wikipedia)](https://en.wikipedia.org/wiki/Edge_crush_test),
[McKee Formula](http://pkgsolutions.co.uk/boxcomp/bcHelp/McKeeFormula.html),
[Esko: Corrugated Compression Strength](https://docs.esko.com/docs/en-us/cape/18/userguide/en-us/common/cape/concept/co_cape_18_CorrugatedCompressionStrength.html),
[Estimation of the Compressive Strength of Corrugated Board Boxes with Shifted Creases on the Flaps (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8467740/).

**What this means for us:** ECT/BCT give us a *validation target for crushing*, not
a set of PhysX parameters. Quoting an ECT number next to a rigid box would be
decoration. It becomes meaningful only once we can actually crush something.

---

## 2. What the simulator can actually do

Checked against this install (Isaac Sim 6.0.1, PhysX 110.1.13):

| approach | can it express a crease? | verdict here |
| --- | --- | --- |
| Single rigid body | No. No folding at all. | what we have today |
| **Rigid flaps + revolute joints at each crease** | Approximately: a joint drive gives restoring torque, joint limits give the fold range, and a yield rule can move the rest angle once torque exceeds a threshold | **the practical route** |
| Deformable / FEM board | Closest to real board | blocked for manipulation: deformables in Isaac Sim are currently **passive**, and attaching them to rigid articulations is an open feature request, so a robot cannot grip a deformable flap |

Source on the deformable limitation: [IsaacLab discussion #1327 on soft-body support](https://github.com/isaac-sim/IsaacLab/discussions/1327),
and a survey of what simulators model for deformables:
[A Survey of Robotic Navigation and Manipulation with Physics Simulators](https://arxiv.org/pdf/2505.01458).

### The elastic-then-plastic behaviour, concretely

Real board: stiff, then it yields and takes a permanent set. PhysX joints are
elastic -- a drive always pulls back to its target. So permanent creasing is not a
raw physics property; it has to be an explicit rule:

1. Model each crease as a **revolute joint** at the fold line.
2. Give it a **drive** with stiffness and damping: that is the restoring force the
   user described, the resistance you feel before it gives.
3. Watch the joint torque. When it exceeds a **yield threshold**, move the drive's
   **rest angle** toward the current angle and **reduce its stiffness**.
   That is the crease forming, and it reproduces the documented fact that a crease
   is permanently weaker than the board around it.
4. Record that yield threshold as an `uncalibrated_assumption` until it is fitted
   against a real four-point bending (BNT) measurement.

This is a model of the behaviour, not of the material. It must be labelled as such
everywhere it appears, exactly like the mass and friction values already are.

---

## 3. What we are choosing to build, and what we are not

**Not yet.** The handbook (section 17) deliberately sequences flaps, cups and
packaging materials *after* the rigid baseline, and the current stage is S4
(mass properties and coverage). Jumping to articulated flaps now would mean
building crease mechanics on top of a box whose containment result is still
dt-dependent (D017). That is the wrong order.

**The plan**, recorded as a task card so it survives this conversation:
`docs/tasks/EXT1_cardboard_flaps.md`.

**The honest position on our current asset:** it is a rigid open tub with the right
external dimensions and a real cavity. It is a valid test fixture for "can a robot
put an object inside a box", which is the task S2 set out to check. It is *not* a
cardboard box, it has never been calibrated against one, and no run report should
imply otherwise. Every case file already carries
`provenance.dimensions: engineering_example`, which is accurate, and that must not
quietly become `measured`.
