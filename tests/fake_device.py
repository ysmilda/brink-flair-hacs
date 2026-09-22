"""Fakes standing in for the ``brink_flair_modbus`` library."""

from __future__ import annotations

from typing import Any

from brink_flair_modbus import (
    BypassMode,
    BypassStatus,
    ControlMode,
    DateFormat,
    DigitalInputFunction,
    ExternalHeaterMode,
    FanFunction,
    FlowLimits,
    FlowType,
    FrostStatus,
    GeoValveOutput,
    GeoValvePosition,
    Language,
    ModbusInterfaceType,
    ModbusParity,
    ModbusSpeed,
    OperatingMode,
    SignalOutputFunction,
    TimeNotation,
    VentilationLevel,
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
            software_version="S1.01.02.0001",
            hardware_version="H1.1",
            serial_number="123456789012",
        )
        self.measurements = FakeComponent(
            supply_pressure=150.0,
            exhaust_pressure=130.0,
            setpoint_supply_volume=250.0,
            supply_volume=260.0,
            supply_mass_flow=269.0,
            supply_fan_rpm=1450,
            supply_anemometer_rpm=1400,
            supply_temperature=21.3,
            supply_relative_humidity=44.0,
            setpoint_exhaust_volume=250.0,
            exhaust_volume=245.0,
            exhaust_mass_flow=254.0,
            exhaust_fan_rpm=1400,
            exhaust_anemometer_rpm=1350,
            exhaust_temperature=19.8,
            exhaust_relative_humidity=55.0,
            bypass_step_position=1000,
            preheater_capacity=0,
            frost_heater_setpoint=0.0,
            frost_fan_reduction=0,
            outside_temperature=8.2,
            dwelling_temperature=20.5,
            rht_humidity=43.2,
            current_operating_time=40250,
            filter_used_hours=120.5,
            filter_used_volume=18000.0,
            total_flow=350000.0,
            current_time="13:45",
            current_date="21-09",
        )
        self.status = FakeComponent(
            filter_dirty=False,
            operation_mode=OperatingMode.AUTO_MODBUS,
            bypass_status=BypassStatus.CLOSED,
            frost_status=FrostStatus.NO_FROST,
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
            pwm_inlet_0=50,
            pwm_inlet_1=62,
            pwm_inlet_2=75,
            pwm_inlet_3=90,
            pwm_exhaust_0=55,
            pwm_exhaust_1=68,
            pwm_exhaust_2=80,
            pwm_exhaust_3=95,
            flow_type=FlowType.CONSTANT_FLOW,
            switch_default_position=2,
            display_as_switch=False,
            imbalance_allowed=True,
            imbalance_value=5,
            external_heater_mode=ExternalHeaterMode.NOT_AVAILABLE,
            postheater_setpoint=20.0,
            rht_sensor_mode=False,
            rht_sensor_sensitivity=1,
            co2_sensor_mode=False,
            co2_1_low_level=800,
            co2_1_high_level=1200,
            co2_2_low_level=800,
            co2_2_high_level=1200,
            co2_3_low_level=800,
            co2_3_high_level=1200,
            co2_4_low_level=800,
            co2_4_high_level=1200,
            signal_output_function=SignalOutputFunction.OFF,
            cv_connected=False,
            digital_input_1_closed=True,
            digital_input_1_function=DigitalInputFunction.ON,
            digital_input_1_supply_fan=FanFunction.POSITION_SWITCH,
            digital_input_1_exhaust_fan=FanFunction.UNCHANGED,
            digital_input_2_closed=False,
            digital_input_2_function=DigitalInputFunction.OFF,
            digital_input_2_supply_fan=FanFunction.FAN_OFF,
            digital_input_2_exhaust_fan=FanFunction.FAN_OFF,
            analogue_input_1_mode=False,
            analogue_input_1_vmin=0.0,
            analogue_input_1_vmax=10.0,
            analogue_input_2_mode=False,
            analogue_input_2_vmin=0.0,
            analogue_input_2_vmax=10.0,
            geo_exchanger=False,
            geo_minimum_temperature=5.0,
            geo_maximum_temperature=25.0,
            geo_valve_default_position=GeoValvePosition.CLOSED,
            geo_valve_output=GeoValveOutput.RELAY_OUTPUT_1,
            language=Language.ENGLISH,
            date_format=DateFormat.DD_MM_YYYY,
            time_notation=TimeNotation.HOUR_24,
            clock_month_day=1826,
            clock_year=2026,
            clock_time=1345,
            clock_day_seconds=3600,
            modbus_interface_type=ModbusInterfaceType.MODBUS_INTERNAL,
            modbus_slave_address=20,
            modbus_speed=ModbusSpeed.BAUD_19200,
            modbus_parity=ModbusParity.EVEN,
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
