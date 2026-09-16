"""In-runtime entry point for the USD-only steps: build and validate.

Runs under the Isaac venv interpreter because that is where `pxr` lives, but it
never constructs `SimulationApp`, so it costs a couple of seconds and no GPU.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback

from parcel_forge import EXIT_ASSET_FAIL, EXIT_ENV_FAIL, EXIT_OK


def cmd_build(args) -> int:
    from parcel_forge.usd_author import author_open_box

    with open(args.case, encoding="utf-8") as fh:
        case = json.load(fh)
    geom, physics = case["geometry"], case["physics"]
    usd_path = os.path.join(args.out, "asset.usda")
    manifest = author_open_box(
        usd_path,
        geom["outer_size_m"], geom["wall_thickness_m"], geom["fault"],
        body_mode=physics["body_mode"], shell_mass_kg=physics.get("shell_mass_kg"),
        asset_id=case["case_id"],
    )
    manifest["usd_path"] = "asset.usda"  # store relative inside the run
    with open(os.path.join(args.out, "build_manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"[BUILD] wrote {usd_path}", flush=True)
    print(f"[BUILD] plates={manifest['plate_count']} body_mode={manifest['body_mode']} "
          f"interior={manifest['interior_length_m']:.4f}x{manifest['interior_width_m']:.4f}"
          f"x{manifest['interior_height_m']:.4f} m", flush=True)
    return EXIT_OK


def cmd_validate(args) -> int:
    from parcel_forge.validation.static_usd import validate_asset

    with open(args.manifest, encoding="utf-8") as fh:
        expected = json.load(fh)
    with open(args.profile, encoding="utf-8") as fh:
        profile = json.load(fh)

    report = validate_asset(args.asset, expected, profile["tolerances"]["geometry_m"])
    report["profile"] = profile["profile_id"]
    with open(os.path.join(args.out, "validation.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    for c in report["checks"]:
        print(f"[VALIDATE] {c['status']:<8} {c['rule']}: {c['detail']}", flush=True)
    print(f"[VALIDATE] verdict={report['summary']['verdict']} "
          f"failed={report['summary']['failed']} blocked={report['summary']['blocked']}", flush=True)
    return EXIT_OK if report["summary"]["verdict"] == "pass" else EXIT_ASSET_FAIL


def main(argv) -> int:
    parser = argparse.ArgumentParser(description="parcel-forge USD tool (no Kit, no GPU)")
    sub = parser.add_subparsers(dest="command", required=True)

    b = sub.add_parser("build")
    b.add_argument("--case", required=True)
    b.add_argument("--out", required=True)
    b.set_defaults(func=cmd_build)

    v = sub.add_parser("validate")
    v.add_argument("--asset", required=True)
    v.add_argument("--manifest", required=True)
    v.add_argument("--profile", required=True)
    v.add_argument("--out", required=True)
    v.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception:
        traceback.print_exc()
        return EXIT_ENV_FAIL


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
