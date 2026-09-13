"""Device-type codes reported by a Brink Flair unit (register 4004).

Register 4004 does not return the model number. It returns an opaque
*device-type* code; the Brink Modbus manual (UWA2-B/UWA2-E) describes it as
"an internal number representing the functional appliance. It has no external
value." A Flair 300, for example, reports the code ``24`` rather than ``300``.

Brink never documents these codes, so the mapping below is assembled from
unit reports rather than guessed, and is deliberately incomplete:

    Device type | Model
    ------------+--------
    24          | 300

Codes that are unknown or not yet read resolve to the most common unit, the
Flair 300, so a compatible device still works.
"""

from __future__ import annotations

#: Raw device-type codes (register 4004) mapped to the Flair model number.
_DEVICE_TYPES: dict[int, int] = {
    24: 300,
}

#: Model used when the code is unknown. The Flair 300, being the most common
#: unit, is the least-surprising default.
DEFAULT_MODEL = 300


def is_known_device_type(device_type: int | None) -> bool:
    """Return whether this device-type code maps to a known Flair model.

    ``None`` (register never read) counts as unknown.
    """
    return device_type in _DEVICE_TYPES


def model_for_device_type(device_type: int | None) -> int | None:
    """Return the Flair model number for a register-4004 device-type code.

    ``None`` is returned only when no code could be read at all; unknown
    codes fall back to the default model so the unit still works.
    """
    if device_type is None:
        return None
    return _DEVICE_TYPES.get(device_type, DEFAULT_MODEL)


def model_name_for_device_type(device_type: int | None) -> str:
    """Return the user-facing model name for a register-4004 device-type code."""
    model = model_for_device_type(device_type)
    if model is None:
        return "Brink Flair"
    return f"Brink Flair {model}"