import math,unittest
from parcel_forge.crease_model import CreaseState,advance
class CreaseTests(unittest.TestCase):
    def test_below_yield_no_plasticity(self):
        state,info=advance(CreaseState(),.5,.01,.04,.03,.08)
        self.assertEqual(state.target,0);self.assertEqual(info['plastic_increment_rad'],0)
    def test_high_load_and_unload_history(self):
        state=CreaseState()
        for _ in range(1000):state,info=advance(state,1.5,.01,.04,.03,.08)
        self.assertGreater(state.target,.7);self.assertLess(state.target,1.5)
        unchanged,_=advance(state,state.target,.01,.04,.03,.08)
        self.assertEqual(unchanged,state)
        reverse,info=advance(state,-1.5,.01,.04,.03,.08)
        self.assertLess(reverse.target,state.target);self.assertGreaterEqual(info['plastic_dissipation_j'],0)
    def test_step_refinement(self):
        def solve(dt):
            state=CreaseState()
            for _ in range(round(2/dt)):state,_=advance(state,1.5,dt,.04,.03,.08,softening_rate=0)
            return state.target
        exact=.75*(1-math.exp(-1))
        self.assertLess(abs(solve(.005)-exact),abs(solve(.02)-exact))
    def test_softening_bounded_and_invariant_to_steps(self):
        state=CreaseState(.3,100)
        _,info=advance(state,.3,.01,.04,.03,.08)
        self.assertEqual(info['yield_torque_nm'],.015)
        self.assertEqual(info['plastic_increment_rad'],0)

    def test_repeated_reversal_softens_until_floor(self):
        state=CreaseState();end_yields=[]
        for cycle in range(4):
            for step in range(1600):
                theta=1.6*math.sin(2*math.pi*step/1600)
                state,info=advance(state,theta,.005,.04,.03,.08)
                self.assertGreaterEqual(info['yield_torque_nm'],.015)
                self.assertLessEqual(info['yield_torque_nm'],.03)
            end_yields.append(info['yield_torque_nm'])
        self.assertGreater(end_yields[0],end_yields[1])
        self.assertEqual(end_yields[-1],.015)
        self.assertGreater(state.accumulated_plastic,0)

class RateIndependentTests(unittest.TestCase):
    def test_zero_viscosity_returns_the_trial_torque_to_the_yield_surface(self):
        state,info=advance(CreaseState(),1.5,.01,.04,.03,0.,softening_rate=0)
        self.assertAlmostEqual(state.target,1.5-.03/.04)
        self.assertAlmostEqual(abs(info['trial_elastic_torque_nm']),.04*1.5)
        held,_=advance(state,1.5,.01,.04,.03,0.,softening_rate=0)
        self.assertAlmostEqual(held.target,state.target)

    def test_a_harder_pull_creases_further_in_one_step(self):
        gentle,_=advance(CreaseState(),1.0,.01,.04,.03,0.,softening_rate=0)
        hard,_=advance(CreaseState(),1.5,.01,.04,.03,0.,softening_rate=0)
        self.assertGreater(hard.target,gentle.target)

    def test_below_yield_still_returns_fully_elastic(self):
        state,info=advance(CreaseState(),.5,.01,.04,.03,0.,softening_rate=0)
        self.assertEqual(state.target,0);self.assertEqual(info['plastic_increment_rad'],0)

    def test_negative_viscosity_is_still_rejected(self):
        with self.assertRaises(ValueError):advance(CreaseState(),1.5,.01,.04,.03,-1e-9)
