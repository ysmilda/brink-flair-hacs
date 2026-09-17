"""Fakes standing in for the ``brink_flair_modbus`` library."""

from __future__ import annotations

from typing import Any

from brink_flair_modbus import (
    BypassMode,
    BypassStatus,
    Co2SensorStatus,
    ControlMode,
    EBusPowerStatus,
    FanControlType,
    FanStatus,
    FlowLimits,
    FrostStatus,
    GeoExchangerStatus,
    OperatingMode,
    PreheaterStatus,
    SystemErrorStatus,
    VentilationLevel,
    VentilationMode,
)


class FakeComponent:
    """A library component exposing ``declared_fields`` and decoded values.

    The real library components expose each register field as a typed attribute
    and describe them in ``declared_fields``; the diagnostics report reads them
    back through that mapping.
    """

    def __init__(self, **values: Any) -> None:
        self.declared_fields: dict[str, None] = dict.fromkeys(values)
        for name, value in values.items():
            setattr(self, name, value)


class FakeSettings(FakeComponent):
    """A stand-in for the settings component with an async ``write()``."""

    def __init__(self, **values: Any) -> None:
        super().__init__(**values)
        self.writes: list[tuple[str, Any]] = []

    async def write(self, attribute: str, value: Any) -> None:
        """Record the write and apply it to the fake register."""
        self.writes.append((attribute, value))
        setattr(self, attribute, value)


class FakeBrinkFlair:
    """A stand-in for ``brink_flair_modbus.BrinkFlair``."""

    def __init__(self) -> None:
        self.info = FakeComponent(
            manufacturer="Brink",
            model="Flair 300",
            device_type=24,
            extension_device_type=24,
        )
        self.measurements = FakeComponent(
            supply_pressure=150.0,
            exhaust_pressure=130.0,
            setpoint_supply_volume=250.0,
            supply_volume=260.0,
            supply_mass_flow=120,
            supply_fan_rpm=1450,
            supply_anemometer_rpm=1000,
            supply_temperature=21.3,
            supply_relative_humidity=44.0,
            setpoint_exhaust_volume=250.0,
            exhaust_volume=245.0,
            exhaust_mass_flow=110,
            exhaust_fan_rpm=1400,
            exhaust_anemometer_rpm=990,
            exhaust_temperature=19.8,
            exhaust_relative_humidity=55.0,
            bypass_step_position=1234,
            preheater_capacity=42,
            frost_heater_setpoint=0.0,
            frost_fan_reduction=0,
            outside_temperature=8.2,
            dwelling_temperature=21.5,
            rht_humidity=55.0,
            filter_used_hours=120.5,
            filter_used_volume=18000.0,
            current_operating_time=100000,
            total_flow=305419896,
            extension_temperature=24.5,
            extension_contact_1=True,
            extension_contact_2=False,
            extension_analogue_input_1=5.5,
            extension_analogue_input_2=4.5,
            extension_relay_1=True,
            extension_relay_2=False,
            extension_analogue_output_1=10.0,
            extension_analogue_output_2=0.0,
        )
        self.status = FakeComponent(
            filter_dirty=False,
            operation_mode=OperatingMode.AUTO_MODBUS,
            fan_control_type=FanControlType.CONSTANT_FLOW,
            ventilation_mode=VentilationMode.AUTO,
            supply_fan_status=FanStatus.RUNNING,
            exhaust_fan_status=FanStatus.RUNNING,
            bypass_status=BypassStatus.CLOSED,
            preheater_status=PreheaterStatus.INACTIVE,
            frost_status=FrostStatus.NO_FROST,
            flow_switch_position=2,
            signal_output=0,
            ebus_power_status=EBusPowerStatus.POWER_ON,
            geo_exchanger_status=GeoExchangerStatus.CLOSED,
            co2_1_status=Co2SensorStatus.RUNNING,
            co2_1_value=800,
            co2_2_status=Co2SensorStatus.RUNNING,
            co2_2_value=950,
            co2_3_status=None,
            co2_3_value=None,
            co2_4_status=None,
            co2_4_value=None,
            system_error=SystemErrorStatus.NO_ERROR,
            active_incident=0,
        )
        self.settings = FakeSettings(
            desired_flow_rate=250,
            flow_0=100,
            flow_1=150,
            flow_2=200,
            flow_3=250,
            bypass_boost=False,
            bypass_boost_position=2,
            imbalance_intake=0,
            imbalance_exhaust=0,
            bypass_from_dwelling=20.0,
            bypass_from_outside=10.0,
            bypass_hysteresis=2.0,
            frost_control_temperature=0.0,
            frost_minimum_inlet_temperature=10.0,
            filter_change_days=180,
            control_mode=ControlMode.STEP,
            level=VentilationLevel.MEDIUM,
            bypass_mode=BypassMode.AUTO,
        )
        self.flow_limits = FlowLimits(flow_max=300, modbus_flow_rate_max=280)
        self.filter_used_days = 5.5
        self.exchange_filter_in = 25.5
        self.update_count = 0
        self.standby = False
        self.filter_resets = 0

    async def async_update(self) -> None:
        """Bump the poll counter."""
        self.update_count += 1

    async def async_set_standby(self, on: bool) -> None:
        """Record the standby request."""
        self.standby = on

    async def async_reset_filter(self) -> None:
        """Record the filter reset."""
        self.filter_resets += 1
