"""Analytic reference used by the S1 free-fall check.

If this maths drifts, the S1 tolerance stops meaning anything, so it is pinned
here independently of the simulator.
"""

import math
import unittest

G = 9.81


class TestFreeFall(unittest.TestCase):
    def test_handbook_g0_reference_value(self):
        # Handbook section 10 G0: at t = 0.1 s a body released from rest has
        # fallen about 0.04905 m.
        self.assertAlmostEqual(0.5 * G * 0.1 ** 2, 0.04905, places=6)

    def test_symplectic_euler_overshoot_stays_inside_tolerance(self):
        """Semi-implicit Euler overshoots the analytic drop by 0.5*g*dt*t.

        At dt = 1/240 and t = 0.1 s that is ~2.0 mm, which must stay under the
        3 mm tolerance in profiles/s1_smoke_v1.json. Tightening dt or the
        tolerance without redoing this sum will make S1 flaky.
        """
        dt, t, tolerance = 1.0 / 240.0, 0.1, 0.003
        overshoot = 0.5 * G * dt * t
        self.assertLess(overshoot, tolerance)
        self.assertAlmostEqual(overshoot, 0.0020437, places=6)

    def test_cube_rest_height_is_half_its_edge(self):
        # A 4 cm cube resting on z=0 has its centre at 0.02 m.
        self.assertAlmostEqual(0.04 / 2.0, 0.02, places=9)
        self.assertTrue(math.isfinite(0.02))


if __name__ == "__main__":
    unittest.main()
