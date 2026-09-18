"""Offline intake boundaries; synthetic containers/meshes, never model evidence."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib

from parcel_forge.workflow.image_intake import png_info, obj_info, prepare, collect, ROOT


def png():
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind+data) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b'\x00'+b'\xff\x00\x00'*2+b'\x00'+b'\x00\xff\x00'*2)) + chunk(b'IEND', b'')


class ImageIntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'runs').mkdir()
        self.seq = 0
        def allocate(label):
            self.seq += 1
            out = self.root/'runs'/f'{label}_{self.seq}'
            out.mkdir()
            return str(out)
        self.addCleanup(patch.stopall)
        patch('parcel_forge.workflow.image_intake.make_unique_run_dir', side_effect=allocate).start()
        self.bundle = json.loads((ROOT/'contracts/workflow/examples/irregular_rigid.json').read_text())
        self.bundle['task_brief']['initial_state'] = 'resting_on_support'
        self.bundle['parameter_cards'][0]['id'] = 'length'
        for p in self.bundle['parameter_cards']:
            p.update(value=1., provenance='assumed', confidence='low')
        self.bundle_path = self.root/'bundle.json'
        self.image = self.root/'drill.png'
        self.image.write_bytes(png())

    def intake(self):
        self.bundle_path.write_text(json.dumps(self.bundle))
        return prepare(self.bundle_path, self.image, 'synthetic-test-only', 'not-a-real-photo', 'TRELLIS')

    def test_prepared_never_means_generated(self):
        out, result = self.intake()
        self.assertEqual(result['status'], 'prepared')
        self.assertEqual(result['generation'], 'not_tested')
        self.assertFalse(json.loads((out/'request.json').read_text())['generation_authorized'])
        self.assertEqual((out/'input/drill.png').read_bytes(), self.image.read_bytes())

    def test_missing_mass_blocks_input_before_provider(self):
        self.bundle['parameter_cards'][1]['value'] = None
        out, result = self.intake()
        self.assertEqual(result['status'], 'needs_input')
        self.assertFalse((out/'provider_command.json').exists())

    def test_unsupported_behavior_not_silently_removed(self):
        self.bundle['task_brief']['required_behaviors'].append('damage')
        self.bundle['validation_plan']['required_checks'].append('behavior.damage')
        _, result = self.intake()
        self.assertEqual(result['status'], 'unsupported')

    def test_crc_corruption_and_fake_signature_rejected(self):
        data = bytearray(png()); data[-1] ^= 1
        for raw in (bytes(data), b'\x89PNG\r\n\x1a\n'):
            with self.assertRaises(ValueError): png_info(raw)

    def test_oblique_plane_with_3d_bbox_rejected(self):
        p = self.root/'mesh.obj'
        p.write_text('v 0 0 0\nv 1 0 1\nv 1 1 2\nv 0 1 1\nf 1 2 3 4\n')
        with self.assertRaisesRegex(ValueError, 'coplanar'): obj_info(p)

    def test_invalid_indices_rejected(self):
        p = self.root/'mesh.obj'
        p.write_text('v 0 0 0\nv 1 0 0\nv 0 1 1\nf 1 2 9\n')
        with self.assertRaises(ValueError): obj_info(p)

    def test_missing_obj_does_not_accept_glb_name(self):
        out, _ = self.intake()
        patch('parcel_forge.workflow.image_intake.ROOT', self.root).start()
        artifacts = self.root/'artifacts'; artifacts.mkdir()
        (artifacts/'fake.glb').write_bytes(b'not-a-model')
        _, result = collect(out, artifacts)
        self.assertEqual(result['status'], 'conflict')
        self.assertEqual(result['generation'], 'not_tested')

    def test_source_tampering_rejected(self):
        out, _ = self.intake()
        (out/'input/drill.png').write_bytes(b'changed')
        patch('parcel_forge.workflow.image_intake.ROOT', self.root).start()
        _, result = collect(out, self.root)
        self.assertEqual(result['reason'], 'source input hash mismatch')

    def test_handoff_binds_snapshot_without_generation_claim(self):
        out, _ = self.intake()
        patch('parcel_forge.workflow.image_intake.ROOT', self.root).start()
        artifacts = self.root/'artifacts'; artifacts.mkdir()
        # Minimal noncoplanar parser fixture, not the actual image test object.
        (artifacts/'fixture.obj').write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\nf 1 2 3\nf 1 2 4\nf 2 3 4\nf 3 1 4\n')
        handoff, result = collect(out, artifacts)
        self.assertEqual(result['status'], 'artifact_handoff_checked')
        self.assertEqual(result['generation'], 'not_tested')
        self.assertEqual(result['physics'], 'not_tested')
        self.assertTrue((handoff/'provider/raw/fixture.obj').is_file())

    def test_destination_inside_artifact_source_rejected(self):
        out, _ = self.intake()
        patch('parcel_forge.workflow.image_intake.ROOT', self.root).start()
        _, result = collect(out, self.root)
        self.assertEqual(result['status'], 'conflict')
        self.assertIn('destination run', result['reason'])

    def test_artifact_symlink_rejected(self):
        out, _ = self.intake()
        patch('parcel_forge.workflow.image_intake.ROOT', self.root).start()
        artifacts = self.root/'artifacts'; artifacts.mkdir()
        (artifacts/'linked.obj').symlink_to(self.image)
        _, result = collect(out, artifacts)
        self.assertEqual(result['status'], 'conflict')
        self.assertIn('symlinks', result['reason'])


if __name__ == '__main__':
    unittest.main()
