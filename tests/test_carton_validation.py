import math,unittest
from parcel_forge.crease_model import CreaseState
from parcel_forge.validation.carton import evaluate_carton,trailing_angle_spans

NAMES=['HingeMajorYN','HingeMajorYP','HingeMinorXP','HingeMinorXN']
PROFILE={'major_loading_end_s':3,'minor_loading_end_s':6,'major_hold_angle_rad':1.65,'peak_min_deg':60,'plastic_min_deg':10,'residual_min_deg':10,'settled_max_rad_s':.02}


def rows_for(angles_by_joint,dt=.1):
    """angles_by_joint: name -> list of angles, one per step."""
    rows=[]
    for step in range(len(next(iter(angles_by_joint.values())))):
        for name in NAMES:
            angle=angles_by_joint[name][step]
            rows.append([step,step*dt,name,angle,0.0,0.0,0.0,.03,0.0,0.0])
    return rows


def resting(value,steps=40):return [min(value,value*i/10) for i in range(1,steps+1)]


class SettleMetricTests(unittest.TestCase):
    def config(self,scenario='opening-order'):return {'dt_s':.1,'scenario':scenario,'opening_profile':dict(PROFILE)}

    def evaluate(self,rows,vel,scenario='opening-order',final=None,peak=None,states=None,maxplastic=None):
        return evaluate_carton(self.config(scenario),NAMES,rows,peak or [1.8]*4,maxplastic or [.5]*4,
                               states or [CreaseState(1.0,1.0) for _ in NAMES],final or [.5]*4,vel)

    def test_stale_velocity_readback_does_not_block_a_frozen_flap(self):
        # Measured artefact from runs/20260917T105836Z_ext1_carton: the angle is
        # bit-identical for seconds while the DOF velocity readback holds 0.2652 rad/s.
        rows=rows_for({name:resting(.28) for name in NAMES})
        result=self.evaluate(rows,[.2651888430118561,0.,0.,0.])
        self.assertTrue(result['checks']['settled'])
        self.assertFalse(result['settle_metrics']['velocity_readback_settled'])
        self.assertEqual(result['settle_metrics']['velocity_readback_rad_s'][0],.2651888430118561)
        self.assertEqual(result['status'],'pass')

    def test_a_flap_still_moving_is_not_settled(self):
        drifting={name:[i*.02 for i in range(40)] for name in NAMES}
        result=self.evaluate(rows_for(drifting),[0.,0.,0.,0.])
        self.assertFalse(result['checks']['settled'])
        self.assertEqual(result['status'],'fail')
        self.assertTrue(result['settle_metrics']['velocity_readback_settled'])

    def test_trailing_span_uses_only_the_window(self):
        moving_then_still={name:[i*.5 for i in range(20)]+[9.5]*20 for name in NAMES}
        spans=trailing_angle_spans(rows_for(moving_then_still),NAMES,1.0)
        self.assertTrue(all(span==0 for span in spans))
        self.assertGreater(max(trailing_angle_spans(rows_for(moving_then_still),NAMES,3.0)),1)

    def test_window_must_be_positive(self):
        with self.assertRaises(ValueError):trailing_angle_spans(rows_for({n:[0.] for n in NAMES}),NAMES,0)

    def test_coupon_settledness_ignores_the_held_major_flaps(self):
        angles={name:resting(.28) for name in NAMES}
        angles['HingeMajorYN']=[i*.02 for i in range(40)]
        config={'dt_s':.1,'scenario':'crease-coupon','opening_profile':dict(PROFILE)}
        result=evaluate_carton(config,NAMES,rows_for(angles),[1.8]*4,[0.,.5,0.,.5],
                               [CreaseState(1.,1.) for _ in NAMES],[.1,.5,.05,.5],[0.]*4)
        self.assertFalse(result['checks']['settled'])
        self.assertTrue(result['coupon_checks']['settled'])
        self.assertEqual(result['coupon_diagnostic_status'],'pass')
        self.assertEqual(result['status'],'pass')


class LegacyMixedTests(unittest.TestCase):
    def test_legacy_scenario_is_reported_superseded_with_its_checks_intact(self):
        rows=rows_for({name:resting(.28) for name in NAMES})
        result=evaluate_carton({'dt_s':.1,'scenario':'legacy-mixed'},NAMES,rows,[1.8]*4,[0.,.5,0.,0.],
                               [CreaseState() for _ in NAMES],[0.,.28,-.08,-.08],[.265,0.,0.,0.])
        self.assertEqual(result['status'],'superseded')
        self.assertEqual(result['legacy_mixed']['status'],'superseded_by_spec_error')
        self.assertFalse(result['checks']['high_plastic'])
        self.assertFalse(result['checks']['high_retains_open_angle'])
        self.assertTrue(result['checks']['low_no_plastic'])
        self.assertIn('runs/20260917T105836Z_ext1_carton',result['legacy_mixed']['evidence_retained'])

    def test_legacy_status_is_never_pass_even_when_every_check_holds(self):
        rows=rows_for({name:resting(.6) for name in NAMES})
        result=evaluate_carton({'dt_s':.1,'scenario':'legacy-mixed'},NAMES,rows,[1.8]*4,[0.,.5,.5,.5],
                               [CreaseState() for _ in NAMES],[0.,.6,.6,.6],[0.]*4)
        self.assertTrue(all(result['checks'].values()))
        self.assertEqual(result['status'],'superseded')


class ScenarioStatusTests(unittest.TestCase):
    def test_opening_order_status_follows_its_own_checks(self):
        rows=rows_for({name:resting(.5) for name in NAMES})
        config={'dt_s':.1,'scenario':'opening-order','opening_profile':dict(PROFILE)}
        passing=evaluate_carton(config,NAMES,rows,[1.8]*4,[.5]*4,[CreaseState(1.,1.) for _ in NAMES],[.5]*4,[0.]*4)
        self.assertEqual(passing['status'],'pass')
        self.assertNotIn('legacy_mixed',passing)
        shallow=evaluate_carton(config,NAMES,rows,[.5]*4,[.5]*4,[CreaseState(1.,1.) for _ in NAMES],[.5]*4,[0.]*4)
        self.assertFalse(shallow['opening_checks']['all_opened'])
        self.assertEqual(shallow['status'],'fail')

    def test_cyclic_status_needs_both_coupon_and_cyclic_blocks(self):
        steps=300;dt=.1
        angles={name:[.5]*steps for name in NAMES}
        angles['HingeMinorXN']=[(-.2 if any(start<=i*dt<end for start,end in [[6,9],[12,15],[18,21]]) else .5) for i in range(steps)]
        rows=rows_for(angles,dt=dt)
        for row in rows:
            if row[2]=='HingeMinorXN':row[7]=.03-.00005*row[0]
        config={'dt_s':dt,'scenario':'crease-cyclic','opening_profile':dict(PROFILE),
                'cycle_profile':{'opening_intervals_s':[[3,6],[9,12],[15,18],[21,24]],'closing_intervals_s':[[6,9],[12,15],[18,21]],'all_minor_actuators_off_s':24,'yield_floor_nm':.015}}
        result=evaluate_carton(config,NAMES,rows,[1.8]*4,[0.,.5,0.,.5],[CreaseState(1.,1.) for _ in NAMES],[.1,.5,.05,.5],[0.]*4)
        self.assertEqual(result['coupon_diagnostic_status'],'pass')
        self.assertTrue(result['cyclic_checks']['softening_observed'])
        self.assertTrue(result['cyclic_checks']['closing_reversals'])
        self.assertEqual(result['status'],'pass')
        for row in rows:
            if row[2]=='HingeMinorXN':row[7]=.014
        broken=evaluate_carton(config,NAMES,rows,[1.8]*4,[0.,.5,0.,.5],[CreaseState(1.,1.) for _ in NAMES],[.1,.5,.05,.5],[0.]*4)
        self.assertFalse(broken['cyclic_checks']['yield_floor_respected'])
        self.assertEqual(broken['status'],'fail')


if __name__=='__main__':unittest.main()
