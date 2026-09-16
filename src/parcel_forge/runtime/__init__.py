"""Runtime adapters.

One adapter per simulator backend. Everything above this package (schema,
geometry, validation, evidence) must stay backend-agnostic so that adding a
second backend later never rewrites the reports.
"""

from .launcher import IsaacLauncher, build_isaac_command  # noqa: F401
