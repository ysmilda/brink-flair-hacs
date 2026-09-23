"""Tests for the Brink Flair config flow."""

from __future__ import annotations

from typing import Any, Self
from unittest.mock import AsyncMock, patch

from brink_flair_modbus import BrinkProbe
from modbus_connection import ModbusError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.brink_flair.config_flow import BrinkConfigFlow
from custom_components.brink_flair.const import (
    CONF_BAUDRATE,
    CONF_MODEL,
    CONF_UNIT_ID,
    CONF_UPDATE_INTERVAL,
    CONNECTION_SERIAL,
    CONNECTION_TCP,
    DEFAULT_BAUDRATE,
    DEFAULT_PORT,
    DEFAULT_UNIT_ID,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.const import CONF_DEVICE, CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

TCP_DATA: dict[str, Any] = {
    CONF_TYPE: CONNECTION_TCP,
    CONF_HOST: "127.0.0.1",
    CONF_PORT: DEFAULT_PORT,
    CONF_UNIT_ID: DEFAULT_UNIT_ID,
}

SERIAL_DATA: dict[str, Any] = {
    CONF_TYPE: CONNECTION_SERIAL,
    CONF_DEVICE: "/dev/ttyUSB0",
    CONF_BAUDRATE: DEFAULT_BAUDRATE,
    CONF_UNIT_ID: DEFAULT_UNIT_ID,
}


class _FakeTemporaryUnit:
    """Async context manager returned by the patched temporary-unit API."""

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None


async def _init_flow(
    hass: HomeAssistant, *, source: str = SOURCE_USER, entry_id: str | None = None
) -> dict[str, Any]:
    """Start a config flow and return its first result."""
    context: dict[str, str] = {"source": source}
    if entry_id is not None:
        context["entry_id"] = entry_id
    return await hass.config_entries.flow.async_init(DOMAIN, context=context)


async def _menu_to(
    hass: HomeAssistant, result: dict[str, Any], next_step_id: str
) -> dict[str, Any]:
    """Select a transport in the user menu and return the resulting step."""
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": next_step_id}
    )


def _active_flow(hass: HomeAssistant, result: dict[str, Any]) -> BrinkConfigFlow:
    """Return the live flow handler; FlowManager.async_get returns a dict."""
    return hass.config_entries.flow._progress[result["flow_id"]]  # type: ignore[no-any-return]


async def test_user_step_shows_transport_menu(hass: HomeAssistant) -> None:
    """The first user step lets the user pick a transport."""
    result = await _init_flow(hass)
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "user"
    assert result["menu_options"] == ["modbus_tcp", "serial"]


async def test_tcp_known_device_type_creates_entry(hass: HomeAssistant) -> None:
    """A reachable device with a mapped device type creates the entry directly."""

    async def _probe(unit: object) -> BrinkProbe:
        return BrinkProbe(device_type=24)

    with (
        patch(
            "custom_components.brink_flair.config_flow.async_get_temporary_unit",
            return_value=_FakeTemporaryUnit(),
        ),
        patch(
            "custom_components.brink_flair.config_flow.BrinkFlair.async_probe",
            side_effect=_probe,
        ),
        patch(
            "custom_components.brink_flair.async_setup_entry",
            new=AsyncMock(return_value=True),
        ),
    ):
        result = await _menu_to(hass, await _init_flow(hass), "modbus_tcp")
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "modbus_tcp"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "127.0.0.1",
                CONF_PORT: DEFAULT_PORT,
                CONF_UNIT_ID: DEFAULT_UNIT_ID,
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "discovered"
        placeholders = result["description_placeholders"]
        assert placeholders["model"] == "Brink Flair 300"

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Brink Flair 300"
        assert result["data"][CONF_HOST] == "127.0.0.1"
        assert result["data"][CONF_PORT] == DEFAULT_PORT
        assert result["data"][CONF_UNIT_ID] == DEFAULT_UNIT_ID


async def test_tcp_unmapped_device_type_asks_for_model(hass: HomeAssistant) -> None:
    """An unmapped device type asks the user to pick the model."""
    device_type = 99999

    async def _probe(unit: object) -> BrinkProbe:
        return BrinkProbe(device_type=device_type)

    with (
        patch(
            "custom_components.brink_flair.config_flow.async_get_temporary_unit",
            return_value=_FakeTemporaryUnit(),
        ),
        patch(
            "custom_components.brink_flair.config_flow.BrinkFlair.async_probe",
            side_effect=_probe,
        ),
        patch(
            "custom_components.brink_flair.async_setup_entry",
            new=AsyncMock(return_value=True),
        ),
    ):
        result = await _menu_to(hass, await _init_flow(hass), "modbus_tcp")
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "192.168.1.5",
                CONF_PORT: 5020,
                CONF_UNIT_ID: 70,
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "discovered"
        assert "99999" in result["description_placeholders"]["device_type"]

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_MODEL: "400"}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Brink Flair 400"
        assert result["data"][CONF_MODEL] == 400


async def test_tcp_cannot_connect(hass: HomeAssistant) -> None:
    """An unreachable unit keeps the user on the form with a connection error."""

    async def _probe(unit: object) -> BrinkProbe:
        return BrinkProbe(device_type=None)

    with (
        patch(
            "custom_components.brink_flair.config_flow.async_get_temporary_unit",
            return_value=_FakeTemporaryUnit(),
        ),
        patch(
            "custom_components.brink_flair.config_flow.BrinkFlair.async_probe",
            side_effect=_probe,
        ),
    ):
        result = await _menu_to(hass, await _init_flow(hass), "modbus_tcp")
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "192.168.1.5",
                CONF_PORT: DEFAULT_PORT,
                CONF_UNIT_ID: DEFAULT_UNIT_ID,
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "modbus_tcp"
        assert result["errors"] == {"base": "cannot_connect"}


async def test_tcp_already_configured_aborts(hass: HomeAssistant) -> None:
    """A second entry for the same unit is rejected."""
    existing = MockConfigEntry(
        domain=DOMAIN, data=TCP_DATA, unique_id="tcp-127.0.0.1-502_20"
    )
    existing.add_to_hass(hass)

    async def _probe(unit: object) -> BrinkProbe:
        return BrinkProbe(device_type=24)

    with (
        patch(
            "custom_components.brink_flair.config_flow.async_get_temporary_unit",
            return_value=_FakeTemporaryUnit(),
        ),
        patch(
            "custom_components.brink_flair.config_flow.BrinkFlair.async_probe",
            side_effect=_probe,
        ),
    ):
        result = await _menu_to(hass, await _init_flow(hass), "modbus_tcp")
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "127.0.0.1",
                CONF_PORT: DEFAULT_PORT,
                CONF_UNIT_ID: DEFAULT_UNIT_ID,
            },
        )
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "already_configured"


async def test_serial_device_not_found(hass: HomeAssistant) -> None:
    """An unreachable serial unit shows a device-not-found error."""

    async def _probe(unit: object) -> BrinkProbe:
        return BrinkProbe(device_type=None)

    with (
        patch(
            "custom_components.brink_flair.config_flow.async_get_temporary_unit",
            return_value=_FakeTemporaryUnit(),
        ),
        patch(
            "custom_components.brink_flair.config_flow.BrinkFlair.async_probe",
            side_effect=_probe,
        ),
    ):
        result = await _menu_to(hass, await _init_flow(hass), "serial")
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_DEVICE: "/dev/ttyUSB0",
                CONF_BAUDRATE: DEFAULT_BAUDRATE,
                CONF_UNIT_ID: DEFAULT_UNIT_ID,
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "device_not_found"}


async def test_reconfigure_updates_entry(hass: HomeAssistant) -> None:
    """Reconfiguring a TCP entry updates its transport settings in place."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=TCP_DATA, unique_id="tcp-127.0.0.1-502_20"
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.brink_flair.async_setup_entry",
        new=AsyncMock(return_value=True),
    ):
        result = await _init_flow(
            hass, source=SOURCE_RECONFIGURE, entry_id=entry.entry_id
        )
        assert result["type"] == FlowResultType.MENU
        assert result["step_id"] == "reconfigure"

        result = await _menu_to(hass, result, "modbus_tcp")
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "modbus_tcp"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "10.0.0.5",
                CONF_PORT: 1502,
                CONF_UNIT_ID: 70,
            },
        )
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert entry.data[CONF_HOST] == "10.0.0.5"
        assert entry.data[CONF_PORT] == 1502
        assert entry.data[CONF_UNIT_ID] == 70


async def test_reconfigure_duplicate_aborts(hass: HomeAssistant) -> None:
    """Reconfiguring onto a unique id managed by another entry is rejected."""
    reconfigured = MockConfigEntry(
        domain=DOMAIN, data=TCP_DATA, unique_id="tcp-127.0.0.1-502_20"
    )
    reconfigured.add_to_hass(hass)
    other = MockConfigEntry(
        domain=DOMAIN,
        data={**TCP_DATA, CONF_HOST: "10.0.0.5", CONF_PORT: 1502},
        unique_id="tcp-10.0.0.5-1502_70",
    )
    other.add_to_hass(hass)

    result = await _init_flow(
        hass, source=SOURCE_RECONFIGURE, entry_id=reconfigured.entry_id
    )
    result = await _menu_to(hass, result, "modbus_tcp")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "10.0.0.5",
            CONF_PORT: 1502,
            CONF_UNIT_ID: 70,
        },
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert reconfigured.data[CONF_HOST] == "127.0.0.1"


async def test_reconfigure_serial_shows_suggested_values(hass: HomeAssistant) -> None:
    """Reconfiguring a serial entry pre-fills the form with its settings."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=SERIAL_DATA, unique_id="serial-/dev/ttyUSB0-9600_20"
    )
    entry.add_to_hass(hass)

    result = await _init_flow(hass, source=SOURCE_RECONFIGURE, entry_id=entry.entry_id)
    assert result["type"] == FlowResultType.MENU

    result = await _menu_to(hass, result, "serial")
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "serial"
    assert result["errors"] == {}
    assert result["data_schema"].schema[CONF_DEVICE] is not None


async def test_serial_known_device_creates_entry(hass: HomeAssistant) -> None:
    """A reachable serial unit maps to a discovery step and creates an entry."""

    async def _probe(unit: object) -> BrinkProbe:
        return BrinkProbe(device_type=24)

    with (
        patch(
            "custom_components.brink_flair.config_flow.async_get_temporary_unit",
            return_value=_FakeTemporaryUnit(),
        ),
        patch(
            "custom_components.brink_flair.config_flow.BrinkFlair.async_probe",
            side_effect=_probe,
        ),
        patch(
            "custom_components.brink_flair.async_setup_entry",
            new=AsyncMock(return_value=True),
        ),
    ):
        result = await _menu_to(hass, await _init_flow(hass), "serial")
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "serial"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_DEVICE: "/dev/ttyUSB0",
                CONF_BAUDRATE: DEFAULT_BAUDRATE,
                CONF_UNIT_ID: DEFAULT_UNIT_ID,
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "discovered"
        assert result["description_placeholders"]["model"] == "Brink Flair 300"

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Brink Flair 300"
        assert result["data"][CONF_DEVICE] == "/dev/ttyUSB0"
        assert result["data"][CONF_BAUDRATE] == DEFAULT_BAUDRATE


async def test_tcp_probe_error_shows_cannot_connect(hass: HomeAssistant) -> None:
    """A ModbusError during the probe keeps the user on the TCP form."""
    with (
        patch(
            "custom_components.brink_flair.config_flow.async_get_temporary_unit",
            return_value=_FakeTemporaryUnit(),
        ),
        patch(
            "custom_components.brink_flair.config_flow.BrinkFlair.async_probe",
            side_effect=ModbusError("link down"),
        ),
    ):
        result = await _menu_to(hass, await _init_flow(hass), "modbus_tcp")
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "192.168.1.5",
                CONF_PORT: DEFAULT_PORT,
                CONF_UNIT_ID: DEFAULT_UNIT_ID,
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "modbus_tcp"
        assert result["errors"] == {"base": "cannot_connect"}


async def test_discovered_without_probe_aborts(hass: HomeAssistant) -> None:
    """The discovery step aborts when no probe is stored (defensive branch)."""
    result = await _init_flow(hass)
    flow = _active_flow(hass, result)

    result = await flow.async_step_discovered()
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "unknown"


async def test_discovered_invalid_model_shows_error(hass: HomeAssistant) -> None:
    """An unmapped device type with an uncoercible model shows a validation error."""
    device_type = 99999

    async def _probe(unit: object) -> BrinkProbe:
        return BrinkProbe(device_type=device_type)

    with (
        patch(
            "custom_components.brink_flair.config_flow.async_get_temporary_unit",
            return_value=_FakeTemporaryUnit(),
        ),
        patch(
            "custom_components.brink_flair.config_flow.BrinkFlair.async_probe",
            side_effect=_probe,
        ),
        patch(
            "custom_components.brink_flair.async_setup_entry",
            new=AsyncMock(return_value=True),
        ),
    ):
        result = await _menu_to(hass, await _init_flow(hass), "modbus_tcp")
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "192.168.1.5",
                CONF_PORT: DEFAULT_PORT,
                CONF_UNIT_ID: DEFAULT_UNIT_ID,
            },
        )
        flow = _active_flow(hass, result)

        result = await flow.async_step_discovered({CONF_MODEL: "not-a-model"})
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_model"}


async def _options_default(
    hass: HomeAssistant, entry_id: str, key: str
) -> object:
    """Resolve the pre-filled default the options flow shows for a key."""
    result = await hass.config_entries.options.async_init(entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    for marker in result["data_schema"].schema:
        if marker == key and hasattr(marker, "default"):
            return marker.default()
    raise AssertionError(f"no default found for {key!r}")


async def test_options_flow_sets_update_interval(hass: HomeAssistant) -> None:
    """The options flow stores the polling interval in the entry options."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=TCP_DATA, unique_id="tcp-127.0.0.1-502_20"
    )
    entry.add_to_hass(hass)

    default = await _options_default(hass, entry.entry_id, CONF_UPDATE_INTERVAL)
    assert default == DEFAULT_UPDATE_INTERVAL

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_UPDATE_INTERVAL: 60}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_UPDATE_INTERVAL] == 60


async def test_options_flow_keeps_existing_interval(hass: HomeAssistant) -> None:
    """Re-opening the options flow pre-fills the previously stored interval."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=TCP_DATA,
        options={CONF_UPDATE_INTERVAL: 90},
        unique_id="tcp-127.0.0.1-502_20",
    )
    entry.add_to_hass(hass)

    default = await _options_default(hass, entry.entry_id, CONF_UPDATE_INTERVAL)
    assert default == 90
