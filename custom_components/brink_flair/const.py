"""Constants for the Brink Flair integration."""

from typing import Final

from brink_flair_modbus import ModbusParity, ModbusSpeed

DOMAIN: Final = "brink_flair"

CONF_UNIT_ID: Final = "unit_id"
DEFAULT_UNIT_ID: Final = 20  # the unit's default Modbus station address

CONF_MODEL: Final = "model"  # model the user selected when the code is unknown

# Transport selection (stored under homeassistant.const.CONF_TYPE).
CONNECTION_TCP: Final = "tcp"
CONNECTION_SERIAL: Final = "serial"

# How this integration reaches the unit. These describe the connection only:
# they are never written to the device, so they have to match the unit's own
# line settings, which are changed with Brink's service menu.
CONF_BAUDRATE: Final = "baudrate"
CONF_PARITY: Final = "parity"

DEFAULT_PORT: Final = 502
DEFAULT_BAUDRATE: Final = 19200  # the unit's factory line setting
DEFAULT_PARITY: Final = "E"  # even, as shipped

# The line settings the unit supports, derived from the library enums so the
# config flow can only offer values the unit can actually be running at.
BAUDRATES: Final = tuple(int(member.name[5:]) for member in ModbusSpeed)
PARITIES: Final = {
    {ModbusParity.NONE: "N", ModbusParity.EVEN: "E", ModbusParity.ODD: "O"}[
        member
    ]: label
    for member, label in (
        (ModbusParity.NONE, "None"),
        (ModbusParity.EVEN, "Even"),
        (ModbusParity.ODD, "Odd"),
    )
}

CONF_UPDATE_INTERVAL: Final = "update_interval"
DEFAULT_UPDATE_INTERVAL: Final = 30  # seconds between polls
