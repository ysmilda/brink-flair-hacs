"""Brink Flair ventilation unit access over Modbus.

``BrinkFlair`` wraps the device's four subsystems (identity, measurements,
operating status, settings) around a shared ``modbus_connection`` unit and
pools reads into a small number of Modbus requests.
"""

from __future__ import annotations

from .data_model import NAN_INT16, BrinkComponent
from .device import BrinkFlair, BrinkProbe
from .enums import (
    BypassMode,
    BypassStatus,
    ControlMode,
    FrostStatus,
    OperatingMode,
    VentilationLevel,
)
from .exceptions import BrinkValueValidationError
from .flow_limits import DEFAULT_FLOW_LIMITS, FlowLimits, flow_limits_for
from .metadata import attach_metadata
from .subsystems import (
    DeviceInformation,
    Measurements,
    Settings,
    Status,
)

__all__ = [
    "DEFAULT_FLOW_LIMITS",
    "NAN_INT16",
    "BrinkComponent",
    "BrinkFlair",
    "BrinkProbe",
    "BrinkValueValidationError",
    "BypassMode",
    "BypassStatus",
    "ControlMode",
    "DeviceInformation",
    "FlowLimits",
    "FrostStatus",
    "Measurements",
    "OperatingMode",
    "Settings",
    "Status",
    "VentilationLevel",
    "attach_metadata",
    "flow_limits_for",
]
