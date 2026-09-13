"""The top-level BrinkFlair device object."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from modbus_connection import ModbusError
from modbus_connection.model import Component, ComponentGroup

from .flow_limits import FlowLimits, flow_limits_for
from .subsystems import (
    DeviceInformation,
    Measurements,
    Settings,
    Status,
)

if TYPE_CHECKING:
    from modbus_connection._protocol import ModbusUnit


@dataclass(frozen=True)
class BrinkProbe:
    """Result of the safe setup probe."""

    device_type: int | None

    @property
    def model_name(self) -> str:
        """Return the user-facing model name."""
        if self.device_type is None:
            return "Brink Flair"
        return f"Brink Flair {self.device_type}"


class BrinkFlair:
    """A Brink Flair ventilation unit."""

    def __init__(self, unit: ModbusUnit) -> None:
        self._unit = unit
        self.info = DeviceInformation(unit)
        self.measurements = Measurements(unit)
        self.status = Status(unit)
        self.settings = Settings(unit)
        self._group = ComponentGroup(unit, self.components)
        self._reset_filter_pending = False

    @classmethod
    async def async_probe(cls, unit: ModbusUnit) -> BrinkProbe:
        """Read only the identity register needed for setup."""
        try:
            (device_type,) = await unit.read_input_registers(4004, 1)
        except ModbusError:
            return BrinkProbe(device_type=None)
        return BrinkProbe(device_type=int(device_type))

    @property
    def components(self) -> tuple[Component, ...]:
        """Return every actively polled subsystem."""
        return (self.info, self.measurements, self.status, self.settings)

    @property
    def flow_limits(self) -> FlowLimits:
        """Return the airflow envelope for the unit's reported model."""
        return flow_limits_for(self.info.device_type)

    @property
    def filter_used_days(self) -> float | None:
        """Return the elapsed filter lifetime in days."""
        return self.measurements.filter_used_days

    @property
    def exchange_filter_in(self) -> float | None:
        """Return how many days remain until the filter is due."""
        used_days = self.filter_used_days
        change_days = self.settings.filter_change_days
        if used_days is None or change_days is None:
            return None
        return change_days - used_days

    async def async_update(self) -> None:
        """Refresh all active subsystems in pooled Modbus reads."""
        await self._group.async_update()

    async def async_reset_filter(self, delay: float = 2.0) -> None:
        """Pulse the filter reset bit for ``delay`` seconds.

        The unit resets its filter counter on the rising edge of register
        8010 bit 0, so the write is held for ``delay`` before being cleared.
        """
        if self._reset_filter_pending:
            return
        self._reset_filter_pending = True
        try:
            await self.settings.write("reset_filter", True)
            await asyncio.sleep(delay)
            await self.settings.write("reset_filter", False)
        finally:
            self._reset_filter_pending = False

    async def async_set_standby(self, enabled: bool) -> None:
        """Place the unit in standby, or back into normal operation.

        Register 8003 is written with ``1`` (standby) or ``2`` (normal), the
        only semantics the reference config relies on; the unit does not
        report the command back, so state is tracked optimistically.
        """
        await self._unit.write_register(8003, 1 if enabled else 2)
