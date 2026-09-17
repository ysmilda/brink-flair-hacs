"""Tests for the binary sensor platform."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .fake_device import FakeBrinkFlair
from .platform_setup import async_setup_brink_flair


def _registry_entry(
    hass: HomeAssistant, entry_id: str, key: str
) -> er.RegistryEntry | None:
    """Return the registry entry for a binary sensor ``key``."""
    registry = er.async_get(hass)
    return registry.async_get_entity_id(
        "binary_sensor", "brink_flair", f"{entry_id}_{key}"
    )


async def test_clean_filter_off(hass: HomeAssistant) -> None:
    """A clean filter reports the problem binary sensor off."""
    _ = await async_setup_brink_flair(hass)

    state = hass.states.get("binary_sensor.flair_300_filter_dirty")
    assert state is not None
    assert state.state == "off"


async def test_dirty_filter_on(hass: HomeAssistant) -> None:
    """An expired counter turns the problem binary sensor on."""
    entry, device = await async_setup_brink_flair(hass)
    device.status.filter_dirty = True
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.flair_300_filter_dirty")
    assert state is not None
    assert state.state == "on"


async def test_unknown_filter_state(hass: HomeAssistant) -> None:
    """An unread counter reports an unknown binary sensor."""
    entry, device = await async_setup_brink_flair(hass)
    device.status.filter_dirty = None
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.flair_300_filter_dirty")
    assert state is not None
    assert state.state == "unknown"


async def test_signal_output_disabled_by_default(hass: HomeAssistant) -> None:
    """The signal output is registered, but only as a disabled diagnostic."""
    entry, _ = await async_setup_brink_flair(hass)

    entity_id = _registry_entry(hass, entry.entry_id, "status_signal_output")
    assert entity_id is not None
    assert hass.states.get("binary_sensor.flair_300_signal_output") is None

    registry = er.async_get(hass)
    entry = registry.async_get(entity_id)
    assert entry is not None
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION


async def test_extension_inputs_with_module(hass: HomeAssistant) -> None:
    """The extension inputs are registered while the module is present."""
    entry, _ = await async_setup_brink_flair(hass)

    registry = er.async_get(hass)
    for key in (
        "measurements_extension_contact_1",
        "measurements_extension_contact_2",
        "measurements_extension_relay_1",
        "measurements_extension_relay_2",
    ):
        entity_id = _registry_entry(hass, entry.entry_id, key)
        assert entity_id is not None
        assert (
            hass.states.get(
                f"binary_sensor.flair_300_{key.removeprefix('measurements_')}"
            )
            is None
        )
        assert (
            registry.async_get(entity_id).disabled_by
            is er.RegistryEntryDisabler.INTEGRATION
        )


async def test_extension_inputs_without_module(hass: HomeAssistant) -> None:
    """The extension inputs do not register without the module."""
    device = FakeBrinkFlair()
    device.info.extension_device_type = 0
    entry, _ = await async_setup_brink_flair(hass, device)

    for key in (
        "measurements_extension_contact_1",
        "measurements_extension_contact_2",
        "measurements_extension_relay_1",
        "measurements_extension_relay_2",
    ):
        assert _registry_entry(hass, entry.entry_id, key) is None
        assert (
            hass.states.get(
                f"binary_sensor.flair_300_{key.removeprefix('measurements_')}"
            )
            is None
        )


async def test_extension_inputs_drop_with_module(hass: HomeAssistant) -> None:
    """The extension inputs disappear once the module reports absent."""
    entry, device = await async_setup_brink_flair(hass)

    assert (
        _registry_entry(hass, entry.entry_id, "measurements_extension_contact_1")
        is not None
    )

    device.info.extension_device_type = 0
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    for key in (
        "measurements_extension_contact_1",
        "measurements_extension_contact_2",
        "measurements_extension_relay_1",
        "measurements_extension_relay_2",
    ):
        assert _registry_entry(hass, entry.entry_id, key) is None

    device.info.extension_device_type = 24
    entry.runtime_data.async_set_updated_data(device)
    await hass.async_block_till_done()

    assert (
        _registry_entry(hass, entry.entry_id, "measurements_extension_contact_1")
        is not None
    )
