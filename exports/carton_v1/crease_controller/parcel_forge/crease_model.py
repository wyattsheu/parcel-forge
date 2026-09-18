"""Uncalibrated viscoplastic hinge state, in SI/radian units."""
from dataclasses import dataclass
import math

@dataclass
class CreaseState:
    target: float=0.0
    accumulated_plastic: float=0.0


def advance(state,theta,dt,stiffness,yield_torque,plastic_viscosity,softening_rate=0.15,min_yield_fraction=0.5):
    """plastic_viscosity 0 is the rate-independent limit: the step then returns the
    trial torque exactly onto the yield surface, so a harder pull creases further in
    the same step instead of requiring the flap to be held for seconds."""
    values=(theta,dt,stiffness,yield_torque,plastic_viscosity,softening_rate,min_yield_fraction,state.target,state.accumulated_plastic)
    if not all(math.isfinite(v) for v in values) or min(dt,stiffness,yield_torque)<=0 or plastic_viscosity<0 or softening_rate<0 or not 0<min_yield_fraction<=1:
        raise ValueError('invalid hinge parameters/state')
    current_yield=yield_torque*max(min_yield_fraction,math.exp(-softening_rate*state.accumulated_plastic))
    trial=stiffness*(theta-state.target)
    # Backward Euler plastic flow for a fixed angle over this step. Bound avoids overshoot.
    delta=math.copysign(max(0.0,abs(trial)-current_yield)*dt/(plastic_viscosity+stiffness*dt),trial)
    new=CreaseState(state.target+delta,state.accumulated_plastic+abs(delta))
    return new,{'trial_elastic_torque_nm':trial,'yield_torque_nm':current_yield,'plastic_increment_rad':delta,'plastic_dissipation_j':abs(trial*delta)}
