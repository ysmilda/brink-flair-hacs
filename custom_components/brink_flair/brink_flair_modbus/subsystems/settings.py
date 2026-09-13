"""Writing registers of a Brink Flair unit (holding registers)."""

from __future__ import annotations

from ..data_model import BrinkComponent, bit, enum, gauge, integer
from ..enums import BypassMode, ControlMode, VentilationLevel
from ..flow_limits import MAX_FLOW, MAX_MODBUS_FLOW_RATE

_SETTINGS_RANGES = (
    (6000, 6000),
    (6001, 6001),
    (6002, 6002),
    (6003, 6003),
    (6035, 6035),
    (6036, 6036),
    (6100, 6100),
    (6101, 6101),
    (6102, 6102),
    (6103, 6103),
    (6104, 6104),
    (6105, 6105),
    (6110, 6110),
    (6111, 6111),
    (6120, 6120),
    (8000, 8000),
    (8001, 8001),
    (8002, 8002),
    (8010, 8010),
)


class Settings(BrinkComponent):
    """Writable airflow and filter settings of the unit."""

    register_space = "holding"
    register_ranges = _SETTINGS_RANGES

    flow_0 = integer(
        6000,
        signed=True,
        writable=True,
        unit="m³/h",
        min_value=0,
        max_value=MAX_FLOW,
        description="Configured volume flow for step 0",
    )
    flow_1 = integer(
        6001,
        signed=True,
        writable=True,
        unit="m³/h",
        min_value=50,
        max_value=MAX_FLOW,
        description="Configured volume flow for step 1",
    )
    flow_2 = integer(
        6002,
        signed=True,
        writable=True,
        unit="m³/h",
        min_value=50,
        max_value=MAX_FLOW,
        description="Configured volume flow for step 2",
    )
    flow_3 = integer(
        6003,
        signed=True,
        writable=True,
        unit="m³/h",
        min_value=50,
        max_value=MAX_FLOW,
        description="Configured volume flow for step 3",
    )
    # Fan imbalance trim, in tenths of a percent (register value x10).
    imbalance_intake = gauge(
        6035,
        0.1,
        signed=True,
        writable=True,
        unit="%",
        min_value=-15,
        max_value=15,
        step=1,
        description="Intake fan balance trim relative to a balanced rig",
    )
    imbalance_exhaust = gauge(
        6036,
        0.1,
        signed=True,
        writable=True,
        unit="%",
        min_value=-15,
        max_value=15,
        step=1,
        description="Exhaust fan balance trim relative to a balanced rig",
    )
    bypass_mode = enum(
        6100,
        BypassMode,
        writable=True,
        description="User selection that overrides the automatic bypass",
    )
    # Bypass control temperatures, in tenths of a degree (register value x10).
    bypass_from_dwelling = gauge(
        6101,
        0.1,
        signed=True,
        writable=True,
        unit="°C",
        min_value=15,
        max_value=35,
        step=0.5,
        description="Indoor temperature above which the bypass may open",
    )
    bypass_from_outside = gauge(
        6102,
        0.1,
        signed=True,
        writable=True,
        unit="°C",
        min_value=7,
        max_value=15,
        step=0.5,
        description="Outdoor temperature below which the bypass stays shut",
    )
    bypass_hysteresis = gauge(
        6103,
        0.1,
        signed=True,
        writable=True,
        unit="°C",
        min_value=0,
        max_value=5,
        step=0.5,
        description="Temperature hysteresis of the bypass logic",
    )
    bypass_boost = bit(
        6104,
        0,
        writable=True,
        description="Boost that opens the bypass while it is active",
    )
    bypass_boost_position = integer(
        6105,
        signed=True,
        writable=True,
        min_value=0,
        max_value=3,
        description="Fan position used while bypass boost is active",
    )
    # Frost-protection temperature thresholds, in tenths of a degree.
    frost_control_temperature = gauge(
        6110,
        0.1,
        signed=True,
        writable=True,
        unit="°C",
        min_value=-1.5,
        max_value=1.5,
        step=0.5,
        description="Temperature at which frost protection starts",
    )
    frost_minimum_inlet_temperature = gauge(
        6111,
        0.1,
        signed=True,
        writable=True,
        unit="°C",
        min_value=7,
        max_value=17,
        step=0.5,
        description="Coldest inlet air allowed before fan reduction",
    )
    filter_change_days = integer(
        6120,
        signed=True,
        writable=True,
        min_value=0,
        max_value=365,
        description="Days until the filter warning should appear",
    )
    control_mode = enum(
        8000,
        ControlMode,
        writable=True,
        description="The unit's control mode",
    )
    level = enum(
        8001,
        VentilationLevel,
        writable=True,
        description="The manual ventilation level",
    )
    desired_flow_rate = integer(
        8002,
        signed=False,
        writable=True,
        unit="m³/h",
        min_value=0,
        max_value=MAX_MODBUS_FLOW_RATE,
        description="Target volume flow in Flow mode",
    )
    reset_filter = bit(
        8010,
        0,
        writable=True,
        description="Pulse to reset the filter counter",
    )
