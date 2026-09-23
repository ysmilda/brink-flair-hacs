"""Constants for the Brink Flair integration."""

from typing import Final

DOMAIN: Final = "brink_flair"

CONF_UNIT_ID: Final = "unit_id"
DEFAULT_UNIT_ID: Final = 20  # the unit's default Modbus station address

CONF_MODEL: Final = "model"  # model the user selected when the code is unknown

# Transport selection (stored under homeassistant.const.CONF_TYPE).
CONNECTION_TCP: Final = "tcp"
CONNECTION_SERIAL: Final = "serial"

# Serial-only options.
CONF_BAUDRATE: Final = "baudrate"

DEFAULT_PORT: Final = 502
DEFAULT_BAUDRATE: Final = 19200  # the unit's factory line setting

CONF_UPDATE_INTERVAL: Final = "update_interval"
DEFAULT_UPDATE_INTERVAL: Final = 30  # seconds between polls
