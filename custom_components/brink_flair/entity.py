"""Base entity for Brink Flair."""

from typing import Any, override

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
        self._pending_value: Any = None
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
    def pending_value(self) -> Any:
        """The value of the last write the coordinator has not confirmed yet."""
        return self._pending_value

    def _pending_write(self, value: Any) -> None:
        """Show ``value`` in the UI until the next refresh confirms the write.

        Passing ``None`` retracts a pending value, restoring the live reading.
        """
        self._pending_value = value

    @override
    def _handle_coordinator_update(self) -> None:
        self._pending_value = None
        super()._handle_coordinator_update()

    @property
    def _subsystem(self) -> object:
        """The library sub-system object this entity reads from."""
        if self._component == "device":
            return self.coordinator.device
        return getattr(self.coordinator.device, self._component)
