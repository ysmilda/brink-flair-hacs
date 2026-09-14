"""Base entity for Brink Flair."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BrinkCoordinator


class BrinkEntity(CoordinatorEntity[BrinkCoordinator]):
    """Common identity + device-info for every Brink Flair entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: BrinkCoordinator, key: str, component: str) -> None:
        super().__init__(coordinator)
        self._component = component
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        info = coordinator.device.info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=info.manufacturer,
            model=info.model,
            name=info.model,
        )

    @property
    def _subsystem(self) -> object:
        """The library sub-system object this entity reads from."""
        if self._component == "device":
            return self.coordinator.device
        return getattr(self.coordinator.device, self._component)
