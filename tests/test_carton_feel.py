import json,math,unittest
from pathlib import Path
from parcel_forge.carton_feel import flap_geometry,crease_feel,derive_crease,derive_carton_creases,segment_stability,report
from parcel_forge.crease_model import CreaseState,advance

ROOT=Path(__file__).resolve().parents[1]
MATERIAL=json.loads((ROOT/'config/materials/b_flute_130tl.json').read_text())
BASE={'length_m':.30,'width_m':.20,'height_m':.15,'thickness_m':MATERIAL['thickness_m'],'dt_s':1/240,
      'flap_tip_clearance_m':.0005,'flap_side_clearance_m':.004,'material':MATERIAL,
      'equivalent_density_kg_m3':MATERIAL['areal_mass_kg_m2']/MATERIAL['thickness_m']}


class FeelTests(unittest.TestCase):
    def test_the_old_gains_needed_a_43_degree_pull_before_anything_creased(self):
        config=dict(BASE,stiffness_nm_rad=.04,yield_torque_nm=.03,plastic_viscosity_nm_s_rad=.08)
        feel=crease_feel(config,flap_geometry(config))
        self.assertGreater(feel['yield_angle_deg'],40)
        self.assertGreater(feel['residual_over_self_weight'],5)
        self.assertGreater(feel['seconds_to_crease_45_deg_at_full_load'],5)

    def test_derived_gains_crease_early_and_hold_their_own_weight(self):
        derived=derive_carton_creases(BASE,springback_deg=4.,residual_over_self_weight=1.5)
        config=dict(BASE,**derived);config.update(**{k:derived['crease_gains']['MajorYN'][k] for k in ['stiffness_nm_rad','yield_torque_nm','plastic_viscosity_nm_s_rad']})
        feel=crease_feel(config,flap_geometry(config))
        self.assertAlmostEqual(feel['yield_angle_deg'],4.)
        self.assertAlmostEqual(feel['residual_over_self_weight'],1.5)
        self.assertLess(feel['seconds_to_crease_45_deg_at_full_load'],.1)
        self.assertLess(feel['hinge_omega_dt'],.3)

    def test_every_flap_springs_back_the_same_angle_whatever_its_width(self):
        gains=derive_carton_creases(BASE,springback_deg=4.)['crease_gains']
        angles={name:g['yield_torque_nm']/g['stiffness_nm_rad'] for name,g in gains.items()}
        self.assertAlmostEqual(max(angles.values()),min(angles.values()))
        self.assertGreater(gains['MajorYN']['stiffness_nm_rad'],gains['MinorXP']['stiffness_nm_rad'])
        self.assertAlmostEqual(gains['MajorYN']['stiffness_nm_rad']/gains['MajorYN']['width_m'],
                               gains['MinorXP']['stiffness_nm_rad']/gains['MinorXP']['width_m'])

    def test_derivation_rejects_impossible_targets(self):
        geometry=flap_geometry(BASE)
        for kwargs in [{'springback_deg':0},{'springback_deg':90},{'residual_over_self_weight':0},{'plastic_time_s':-1}]:
            with self.assertRaises(ValueError):derive_crease(geometry,**kwargs)

    def test_a_stiff_board_cut_into_light_strips_is_not_integrable(self):
        unstable=segment_stability(21.19,5.92e-07,1/240)
        self.assertFalse(unstable['stable'])
        self.assertGreater(unstable['omega_dt'],20)
        self.assertLess(unstable['max_stable_stiffness_nm_rad'],unstable['stiffness_nm_rad'] if 'stiffness_nm_rad' in unstable else 21.19)
        self.assertTrue(segment_stability(.002,5.92e-07,1/240)['stable'])

    def test_report_flags_the_recorded_strip_asset_as_unstable(self):
        config=json.loads((ROOT/'runs/20260917T123830Z_ext1_independent_interaction/config.json').read_text())
        out=report(config)
        self.assertFalse(out['panel_segment']['stable'])
        self.assertGreater(out['crease']['yield_angle_deg'],40)


class DerivedGainsBehaveTests(unittest.TestCase):
    """The derived gains driven through the crease law itself, no simulator."""
    def setUp(self):
        self.gains=derive_carton_creases(BASE,springback_deg=4.,residual_over_self_weight=1.5)['crease_gains']['MajorYN']

    def advance_to(self,angle,steps=400):
        state=CreaseState()
        for _ in range(steps):
            state,info=advance(state,angle,1/240,self.gains['stiffness_nm_rad'],self.gains['yield_torque_nm'],
                               self.gains['plastic_viscosity_nm_s_rad'],softening_rate=0)
        return state

    def test_one_tenth_of_a_second_of_pull_is_enough_to_crease(self):
        state=CreaseState()
        for _ in range(24):
            state,_=advance(state,math.radians(90),1/240,self.gains['stiffness_nm_rad'],self.gains['yield_torque_nm'],
                            self.gains['plastic_viscosity_nm_s_rad'],softening_rate=0)
        self.assertGreater(math.degrees(state.target),80)

    def test_springback_is_the_target_angle(self):
        state=self.advance_to(math.radians(60))
        self.assertAlmostEqual(math.degrees(math.radians(60)-state.target),4.,places=1)


class GrabPointTests(unittest.TestCase):
    def config(self):
        derived=derive_carton_creases(BASE,springback_deg=4.,residual_over_self_weight=1.5)
        return dict(BASE,**derived)

    def test_grabbing_halfway_up_the_flap_needs_twice_the_force(self):
        from parcel_forge.carton_feel import grab_force_table
        rows={row['grab_fraction_of_flap']:row['force_n'] for row in grab_force_table(self.config())['by_grab_point']}
        self.assertAlmostEqual(rows[.5],2*rows[1.])
        self.assertAlmostEqual(rows[.25],4*rows[1.])

    def test_the_predicted_tip_force_matches_what_the_simulation_measured(self):
        from parcel_forge.carton_feel import grab_force_table
        predicted=grab_force_table(self.config())['by_grab_point'][0]['force_n']
        # runs/20260917T133338Z_ext1_carton_pull measured 0.16 N in 0.02 N ramp steps.
        self.assertLess(abs(predicted-.16),.02+.01)

    def test_grab_fractions_must_be_on_the_flap(self):
        from parcel_forge.carton_feel import grab_force_table
        for bad in (0,-.5,1.5):
            with self.assertRaises(ValueError):grab_force_table(self.config(),fractions=(bad,))
