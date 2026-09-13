"""Constants for the Brink Flair integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "brink_flair"

CONF_UNIT_ID: Final = "unit_id"
DEFAULT_UNIT_ID: Final = 20  # the unit's default Modbus station address

# Transient identity captured during setup.
CONF_DEVICE_TYPE: Final = "device_type"  # raw register-4004 code
CONF_MODEL: Final = "model"  # model the user selected when the code is unknown

# Transport selection (stored under homeassistant.const.CONF_TYPE).
CONNECTION_TCP: Final = "tcp"
CONNECTION_SERIAL: Final = "serial"

# Serial-only options.
CONF_BAUDRATE: Final = "baudrate"

DEFAULT_PORT: Final = 502
DEFAULT_BAUDRATE: Final = 19200  # the unit's factory line setting

# A ventilation unit changes slowly, but we poll aggressively and fixed.
SCAN_INTERVAL: Final = timedelta(seconds=30)
