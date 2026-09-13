"""Operating status of a Brink Flair unit (input registers)."""

from __future__ import annotations

from ..data_model import BrinkComponent, boolean, enum
from ..enums import BypassStatus, FrostStatus, OperatingMode

_STATUS_RANGES = (
    (4020, 4020),
    (4050, 4050),
    (4070, 4070),
    (4100, 4100),
)


class Status(BrinkComponent):
    """Mode, bypass, frost and filter states of the unit."""

    register_space = "input"
    register_ranges = _STATUS_RANGES

    operation_mode = enum(
        4020,
        OperatingMode,
        description="The unit's current operating mode",
    )
    bypass_status = enum(
        4050,
        BypassStatus,
        description="The heat-recovery bypass position",
    )
    frost_status = enum(
        4070,
        FrostStatus,
        description="The frost-protection state",
    )
    filter_dirty = boolean(
        4100,
        description="Whether the filter counter has expired",
    )
