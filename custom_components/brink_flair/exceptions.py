"""Exceptions raised by the Brink Flair integration."""

from __future__ import annotations

from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN


class BrinkFlairException(HomeAssistantError):
    """Base class for every Brink Flair error."""


class BypassOverrideBlockedError(BrinkFlairException):
    """Raised when a forced bypass would draw cold air in."""

    def __init__(self, supply_volume: float) -> None:
        """Initialize the exception."""
        super().__init__(
            translation_domain=DOMAIN,
            translation_key="bypass_override_blocked",
            translation_placeholders={"supply_volume": str(supply_volume)},
        )
        self.supply_volume = supply_volume
