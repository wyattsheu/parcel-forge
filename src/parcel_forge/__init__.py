"""parcel-forge: reproducible Isaac Sim asset generation and validation workflow.

Stage S0/S1 only. Everything in this package that is not exercised by a saved
run under runs/ is unverified by definition.
"""

__version__ = "0.1.0"

# Project-defined exit codes (handbook section 6). Raw exit codes from external
# tools are stored separately in the run manifest and never reused here.
EXIT_OK = 0
EXIT_ASSET_FAIL = 2
EXIT_ENV_FAIL = 3
EXIT_INSUFFICIENT_EVIDENCE = 4
