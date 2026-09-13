"""Identity registers of a Brink Flair unit (input registers)."""

from __future__ import annotations

from ..data_model import BrinkComponent, integer

_IDENTITY_RANGES = ((4004, 4004),)


class DeviceInformation(BrinkComponent):
    """The unit's identification data (input register space)."""

    register_space = "input"
    register_ranges = _IDENTITY_RANGES

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
        device_type = self._device_type
        if device_type is None:
            return "Brink Flair"
        return f"Brink Flair {device_type}"
