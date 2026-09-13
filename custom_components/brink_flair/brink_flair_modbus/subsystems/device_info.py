"""Identity registers of a Brink Flair unit (input registers)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..data_model import BrinkComponent, integer
from ..device_types import model_name_for_device_type

if TYPE_CHECKING:
    from modbus_connection._protocol import ModbusUnit

_IDENTITY_RANGES = ((4004, 4004),)


class DeviceInformation(BrinkComponent):
    """The unit's identification data (input register space)."""

    register_space = "input"
    register_ranges = _IDENTITY_RANGES

    def __init__(
        self, unit: ModbusUnit, *, model_override: int | None = None
    ) -> None:
        """Initialize and, when the device type is unknown, trust the given model."""
        super().__init__(unit)
        self._model_override = model_override

    _device_type = integer(
        4004,
        signed=False,
        description="The device type reported by the unit",
    )

    @property
    def device_type(self) -> int | None:
        """Return the raw device-type code."""
        return self._device_type

    @property
    def manufacturer(self) -> str:
        """Return the manufacturer name."""
        return "Brink"

    @property
    def model(self) -> str:
        """Return the user-facing model name."""
        if self._model_override is not None:
            return f"Brink Flair {self._model_override}"
        return model_name_for_device_type(self._device_type)
