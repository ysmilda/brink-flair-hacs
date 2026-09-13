"""Airflow and climate measurements of a Brink Flair unit (input registers).

All values are read from the input register space (FC04). Register addresses
are the unit's protocol addresses as published in the Brink Flair Modbus
register map.
"""

from __future__ import annotations

from ..data_model import (
    NAN_INT16,
    BrinkComponent,
    gauge,
    integer,
    uint32,
)

# The ESPHome reference config reads every register on its own, so the
# unit's block-readable spans are not documented. Keep each address its own
# range to guarantee the device never receives an unverifiable multi-word read.
_MEASUREMENT_RANGES = (
    (4023, 4023),
    (4024, 4024),
    (4031, 4031),
    (4032, 4032),
    (4034, 4034),
    (4036, 4036),
    (4037, 4037),
    (4041, 4041),
    (4042, 4042),
    (4044, 4044),
    (4046, 4046),
    (4047, 4047),
    (4071, 4071),
    (4072, 4072),
    (4081, 4081),
    (4115, 4115),
    (4116, 4117),  # 32-bit filter-used counter is a single field span
)


class Measurements(BrinkComponent):
    """Airflow, pressure and climate measurements of the unit."""

    register_space = "input"
    register_ranges = _MEASUREMENT_RANGES

    supply_pressure = integer(
        4023,
        signed=True,
        nan=NAN_INT16,
        unit="Pa",
        description="Static pressure at the supply side",
    )
    exhaust_pressure = integer(
        4024,
        signed=True,
        nan=NAN_INT16,
        unit="Pa",
        description="Static pressure at the exhaust side",
    )
    setpoint_supply_volume = integer(
        4031,
        signed=False,
        unit="m³/h",
        description="The configured supply volume flow set point",
    )
    supply_volume = integer(
        4032,
        signed=False,
        unit="m³/h",
        description="Actual supply volume flow",
    )
    supply_fan_rpm = integer(
        4034,
        signed=False,
        unit="rpm",
        description="Supply fan speed",
    )
    supply_temperature = gauge(
        4036,
        0.1,
        signed=True,
        nan=NAN_INT16,
        unit="°C",
        digits=1,
        description="Temperature of the air supplied to the house",
    )
    supply_relative_humidity = integer(
        4037,
        signed=True,
        unit="%",
        description="Relative humidity of the air supplied to the house",
    )
    setpoint_exhaust_volume = integer(
        4041,
        signed=False,
        unit="m³/h",
        description="The configured exhaust volume flow set point",
    )
    exhaust_volume = integer(
        4042,
        signed=False,
        unit="m³/h",
        description="Actual exhaust volume flow",
    )
    exhaust_fan_rpm = integer(
        4044,
        signed=False,
        unit="rpm",
        description="Exhaust fan speed",
    )
    exhaust_temperature = gauge(
        4046,
        0.1,
        signed=True,
        nan=NAN_INT16,
        unit="°C",
        digits=1,
        description="Temperature of the air exhausted from the house",
    )
    exhaust_relative_humidity = integer(
        4047,
        signed=True,
        unit="%",
        description="Relative humidity of the air exhausted from the house",
    )
    frost_heater_setpoint = integer(
        4071,
        signed=True,
        unit="%",
        description="The frost heater power set point",
    )
    frost_fan_reduction = integer(
        4072,
        signed=True,
        unit="%",
        description="Fan reduction applied during frost protection",
    )
    outside_temperature = gauge(
        4081,
        0.1,
        signed=True,
        nan=NAN_INT16,
        unit="°C",
        digits=1,
        description="Outside temperature",
    )
    filter_used_hours = integer(
        4115,
        signed=False,
        description="Hours of operation counted by the filter counter",
    )
    filter_used_volume = uint32(
        4116,
        unit="m³/h",
        description="Total volume channeled through the filter",
    )

    @property
    def filter_used_days(self) -> float | None:
        """Return the elapsed filter lifetime in days."""
        hours = self.filter_used_hours
        if hours is None:
            return None
        return hours / 24
