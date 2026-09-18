import unittest,math
from parcel_forge.panel_bending import stiffness
class DirectionalBendingTests(unittest.TestCase):
    def test_discretization_preserves_total_rotation(self):
        # Half-cell root plus interior cells reproduces midpoint orientation at tip.
        D,b,L,M=4.26,.05,.2,.03
        for n in (4,8,16):
            h=L/n;rotation=M/stiffness(D,b,h,True)+(n-1)*M/stiffness(D,b,h)
            self.assertAlmostEqual(rotation,M/(D*b)*(L-h/2))
    def test_directional_compliance_ratio(self):
        self.assertAlmostEqual(stiffness(4.26,.05,.025)/stiffness(1.84,.05,.025),4.26/1.84)
    def test_nonphysical_inputs(self):
        for x in (0,-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):stiffness(x,.05,.025)
