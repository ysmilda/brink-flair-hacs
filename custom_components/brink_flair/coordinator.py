"""DataUpdateCoordinator that polls the Brink Flair unit."""

import logging
from typing import override

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from modbus_connection import ModbusError

from .brink_flair_modbus import BrinkFlair
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type BrinkConfigEntry = ConfigEntry[BrinkCoordinator]


class BrinkCoordinator(DataUpdateCoordinator[BrinkFlair]):
    """Refreshes every sub-system on a schedule.

    ``async_update`` fans out to each component (each reads only its own
    registers), so adding/removing entities never changes what is polled. The
    ``modbus`` integration owns the connection; this coordinator only reads.
    """

    config_entry: BrinkConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: BrinkConfigEntry,
        device: BrinkFlair,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=SCAN_INTERVAL,
        )
        self.device = device

    @override
    async def _async_update_data(self) -> BrinkFlair:
        try:
            await self.device.async_update()
        except ModbusError as err:
            raise UpdateFailed(f"Error communicating with Brink Flair: {err}") from err
        return self.device
