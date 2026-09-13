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

from .device_types import model_for_device_type


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

#: Every Flair model the integration knows how to configure.
SUPPORTED_MODELS: tuple[int, ...] = tuple(_FLOW_LIMITS)

#: Full-scale bounds a register write is allowed to reach on any model.
MAX_FLOW = 600
MAX_MODBUS_FLOW_RATE = 600

#: Envelope used for an unknown or not-yet-read device type (the Flair 300,
#: the most common unit).
DEFAULT_FLOW_LIMITS = FlowLimits(300, 280)


def flow_limits_for_model(model: int) -> FlowLimits:
    """Return the airflow envelope for a Flair model number."""
    return _FLOW_LIMITS.get(model, DEFAULT_FLOW_LIMITS)


def flow_limits_for(device_type: int | None) -> FlowLimits:
    """Return the airflow envelope for a device-type code.

    The code reported by register 4004 is an opaque device type, not the model
    number, so it is resolved to a model first (see :mod:`device_types`).
    Device types outside the known family fall back to the Flair 300 envelope
    rather than failing, so an unrecognised unit still works.
    """
    model = model_for_device_type(device_type)
    if model is None:
        return DEFAULT_FLOW_LIMITS
    return flow_limits_for_model(model)
