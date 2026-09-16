"""PNG encoder and blank-frame detection.

The blank check is what stops a black render from being reported as visual
evidence, so it gets a regression test from day one.
"""

import os
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from parcel_forge.pngio import image_stats, write_rgb_png  # noqa: E402


def decode_png(path):
    """Minimal decoder, so the test does not trust the encoder to check itself."""
    with open(path, "rb") as fh:
        blob = fh.read()
    assert blob[:8] == b"\x89PNG\r\n\x1a\n"
    pos, chunks = 8, {}
    while pos < len(blob):
        length = struct.unpack(">I", blob[pos:pos + 4])[0]
        tag = blob[pos + 4:pos + 8]
        data = blob[pos + 8:pos + 8 + length]
        chunks.setdefault(tag, b"")
        chunks[tag] += data
        pos += 12 + length
    w, h, depth, color_type = struct.unpack(">IIBB", chunks[b"IHDR"][:10])
    raw = zlib.decompress(chunks[b"IDAT"])
    channels = 4 if color_type == 6 else 3
    stride = w * channels
    pixels = bytearray()
    for y in range(h):
        row_start = y * (stride + 1)
        assert raw[row_start] == 0, "expected filter type 0"
        pixels += raw[row_start + 1:row_start + 1 + stride]
    return w, h, depth, channels, bytes(pixels)


class TestPng(unittest.TestCase):
    def test_roundtrip_rgb(self):
        w, h = 7, 5
        pixels = bytes((x * 7 + 3) % 256 for x in range(w * h * 3))
        with tempfile.TemporaryDirectory() as tmp:
            path = write_rgb_png(os.path.join(tmp, "a.png"), w, h, pixels)
            dw, dh, depth, channels, out = decode_png(path)
        self.assertEqual((dw, dh, depth, channels), (w, h, 8, 3))
        self.assertEqual(out, pixels)

    def test_roundtrip_rgba(self):
        w, h = 4, 3
        pixels = bytes((x * 11) % 256 for x in range(w * h * 4))
        with tempfile.TemporaryDirectory() as tmp:
            path = write_rgb_png(os.path.join(tmp, "a.png"), w, h, pixels, channels=4)
            dw, dh, _depth, channels, out = decode_png(path)
        self.assertEqual((dw, dh, channels), (w, h, 4))
        self.assertEqual(out, pixels)

    def test_wrong_buffer_size_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                write_rgb_png(os.path.join(tmp, "a.png"), 4, 4, b"\x00" * 10)

    def test_black_frame_is_blank(self):
        stats = image_stats(4, 4, b"\x00" * 48)
        self.assertTrue(stats["looks_blank"])

    def test_flat_colour_is_blank(self):
        stats = image_stats(4, 4, bytes([120, 30, 40] * 16))
        self.assertTrue(stats["looks_blank"])

    def test_varied_frame_is_not_blank(self):
        pixels = bytes((x * 5) % 256 for x in range(4 * 4 * 3))
        self.assertFalse(image_stats(4, 4, pixels)["looks_blank"])


if __name__ == "__main__":
    unittest.main()
