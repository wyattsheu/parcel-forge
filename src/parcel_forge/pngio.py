"""Minimal PNG writer using only the Python standard library.

Pillow may or may not exist in the Isaac runtime; we do not install anything,
so RGB/RGBA buffers are encoded here with zlib + struct instead.
"""

from __future__ import annotations

import struct
import zlib


def _chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def write_rgb_png(path: str, width: int, height: int, pixels: bytes, channels: int = 3) -> str:
    """Write an 8-bit PNG. `pixels` is row-major, top row first, len == w*h*channels."""
    if channels not in (3, 4):
        raise ValueError("channels must be 3 (RGB) or 4 (RGBA)")
    expected = width * height * channels
    if len(pixels) != expected:
        raise ValueError(f"pixel buffer is {len(pixels)} bytes, expected {expected}")

    stride = width * channels
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type 0 (None) for every scanline
        raw += pixels[y * stride : (y + 1) * stride]

    color_type = 6 if channels == 4 else 2
    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    blob = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
        + _chunk(b"IEND", b"")
    )
    with open(path, "wb") as handle:
        handle.write(blob)
    return path


def image_stats(width: int, height: int, pixels: bytes, channels: int = 3) -> dict:
    """Cheap non-blank check: a black or empty render is a render failure, not a pass."""
    rgb = [pixels[i] for i in range(0, len(pixels), channels)]
    if not rgb:
        return {"width": width, "height": height, "mean_r": 0.0, "distinct_r": 0, "looks_blank": True}
    mean_r = sum(rgb) / len(rgb)
    distinct = len(set(rgb))
    return {
        "width": width,
        "height": height,
        "mean_r": round(mean_r, 4),
        "distinct_r": distinct,
        # A single flat colour across the whole frame means we rendered nothing.
        "looks_blank": bool(distinct <= 2 or mean_r < 1.0),
    }
