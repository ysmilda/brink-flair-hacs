"""DataUpdateCoordinator that polls the Brink Flair unit."""

from datetime import timedelta
import logging
from typing import override

from brink_flair_modbus import BrinkFlair
from modbus_connection import ModbusError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

type BrinkConfigEntry = ConfigEntry[BrinkCoordinator]


def _update_interval_for(entry: ConfigEntry) -> timedelta:
    """Return the polling interval configured for ``entry``."""
    return timedelta(
        seconds=entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    )


class BrinkCoordinator(DataUpdateCoordinator[BrinkFlair]):
    config_entry: BrinkConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: BrinkConfigEntry,
        device: BrinkFlair,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=_update_interval_for(entry),
        )
        self.device = device

    def apply_options(self) -> None:
        """Adopt the entry's configured polling interval without reloading."""
        self.update_interval = _update_interval_for(self.config_entry)

    @override
    async def _async_update_data(self) -> BrinkFlair:
        try:
            await self.device.async_update()
        except ModbusError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="communication_error",
                translation_placeholders={"error": str(err)},
            ) from err
        return self.device
