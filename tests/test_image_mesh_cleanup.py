import unittest
from parcel_forge.image_mesh_cleanup import face_components,srgb_to_linear
class MeshAppearanceTests(unittest.TestCase):
 def test_components_use_topology_not_distance(self):
  self.assertEqual(face_components([[0,1,2],[2,1,3],[4,5,6]],7),[[0,1],[2]])
 def test_linear_color_reference_and_boundaries(self):
  self.assertAlmostEqual(srgb_to_linear(.5),.21404114048223255)
  self.assertEqual(srgb_to_linear(0),0);self.assertEqual(srgb_to_linear(1),1)
  with self.assertRaises(ValueError):srgb_to_linear(255)
if __name__=='__main__':unittest.main()
