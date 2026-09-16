"""Validation layers: static geometry, cavity/placement outcome, dynamics.

Nothing in this package may modify an asset, a specification or an acceptance
profile. It only measures and classifies.
"""

from .outcome import classify_probe_outcome  # noqa: F401
