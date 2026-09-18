"""Validation for explicit contact/material settings (standard library only)."""

from __future__ import annotations

import math

FIELDS = ("contact_offset_m", "rest_offset_m", "static_friction",
          "dynamic_friction", "restitution")


def validate_contact_settings(settings: dict) -> list[str]:
    errors = []
    for field in FIELDS:
        value = settings.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"{field} must be a number")
        elif not math.isfinite(value):
            errors.append(f"{field} must be finite")
    if errors:
        return errors
    if settings["contact_offset_m"] < 0:
        errors.append("contact_offset_m must be >= 0")
    if settings["rest_offset_m"] < 0:
        errors.append("rest_offset_m must be >= 0")
    if settings["contact_offset_m"] < settings["rest_offset_m"]:
        errors.append("contact_offset_m must be >= rest_offset_m")
    if settings["static_friction"] < 0 or settings["dynamic_friction"] < 0:
        errors.append("friction coefficients must be >= 0")
    if settings["dynamic_friction"] > settings["static_friction"]:
        errors.append("dynamic_friction must be <= static_friction for this baseline")
    if not 0 <= settings["restitution"] <= 1:
        errors.append("restitution must be between 0 and 1")
    return errors
