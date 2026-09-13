"""Per-model airflow limits of the Brink Flair family.

The Flair exposes a common register map across its models; the airflow
envelope the unit accepts differs per model. These envelopes mirror the
``type_flow_max`` / ``type_modbus_flow_rate_max`` substitutions of the
reference esphome config fonske/Brink-flair-modbus: ``flow_max`` bounds the
per-step registers 6000-6003 and ``modbus_flow_rate_max`` bounds the target
flow register 8002.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FlowLimits:
    """Airflow envelope of one Flair model."""

    flow_max: int
    modbus_flow_rate_max: int


_FLOW_LIMITS: dict[int, FlowLimits] = {
    200: FlowLimits(200, 200),
    225: FlowLimits(225, 225),
    300: FlowLimits(300, 280),
    325: FlowLimits(325, 280),
    400: FlowLimits(400, 400),
    450: FlowLimits(450, 450),
    600: FlowLimits(600, 600),
}

#: Full-scale bounds a register write is allowed to reach on any model.
MAX_FLOW = 600
MAX_MODBUS_FLOW_RATE = 600

#: Envelope used for an unknown or not-yet-read device type (the Flair 300,
#: the most common unit).
DEFAULT_FLOW_LIMITS = FlowLimits(300, 280)


def flow_limits_for(device_type: int | None) -> FlowLimits:
    """Return the airflow envelope for a device-type code.

    Device types outside the known family fall back to the Flair 300
    envelope rather than failing, so an unrecognised unit still works.
    """
    if device_type is None:
        return DEFAULT_FLOW_LIMITS
    return _FLOW_LIMITS.get(device_type, DEFAULT_FLOW_LIMITS)
