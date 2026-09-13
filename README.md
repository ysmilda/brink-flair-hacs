# Brink Flair for Home Assistant (HACS)

Custom integration for the **Brink Flair** (and compatible) ventilation units —
models 200, 225, 300, 325, 400, 450 and 600 — over Modbus.

The integration borrows a Modbus connection from the built-in `modbus`
integration and talks to the unit's register map through the
[`brink-flair-modbus`](https://github.com/ysmilda/brink-flair-modbus) Python
library (published to PyPI). Home Assistant installs it automatically from the
manifest requirements; the `modbus` and `usb` components resolve themselves.

## Install

1. Install via HACS (`Integrations` → ⋯ → *Custom repositories* → this repo, category *Integration*)
   or clone it into `<config>/custom_components/brink_flair/`.
2. Restart Home Assistant.
3. **On the unit** (menu 14 – Communication): `TypeBus=Modbus`, `Slave Address=20`
   (any 1–255, e.g. Viessmann Vitovent units use `70`), `Baudrate=19200`, `Parity=Even`.
   A Flair 300 needs the `TypeBus` set to Modbus and a wired setpoint; the LCD panel
   then shows `EBus` until the first Modbus write, which switches it to `Modelbus`.
4. Add *Brink Flair* via **Settings → Devices & Services**, choose Modbus TCP or
   serial, fill in the host/port (or serial device) and the unit's slave address.
   If the unit's device type (register 4004) isn't mapped yet, the flow asks
   you to pick your model — the choice is saved so the airflow limits match, and
   the step offers links to submit the found device type for the mapping.

## Supported models

Register 4004 does not report the model number; it reports an opaque
*device type* code that the integration maps to a model
(`brink_flair_modbus/device_types.py` in the library repo). Brink never
documents these codes, so the mapping holds only codes verified against real
units; unknown codes fall back to the Flair 300, so a compatible device still
works.

| Device type | Model | Step flow max (m³/h) | Desired flow max (m³/h) |
|------:|------:|-----:|-----:|
| – | 200 | 200 | 200 |
| – | 225 | 225 | 225 |
| 24 | 300 | 300 | 280 |
| – | 325 | 325 | 280 |
| – | 400 | 400 | 400 |
| – | 450 | 450 | 450 |
| – | 600 | 600 | 600 |

Any unrecognised type falls back to the Flair 300 envelope, so a compatible
device still works.

## Entities

- **Sensors** — supply/exhaust/outside temperature, supply/exhaust humidity,
  supply/exhaust pressure, setpoint and actual supply/exhaust volume flow,
  both fan speeds, frost heater power and fan reduction, operating mode,
  bypass and frost status, and the device type.
- **Filter** — used hours/volume/days, days until filter change, a filter
  reset button, and a dirty flag (binary sensor).
- **Controls** — control mode (`Device LCD` / `Modbus Step` / `Modbus Flow`),
  manual level/step, the four per-step flow rates, the desired flow rate
  (Flow mode), bypass mode (forced open/closed with a high-flow guard),
  bypass boost and its fan position switch, intake/exhaust balance trim,
  the bypass temperature thresholds (inside, outside, hysteresis), the frost
  thresholds (control temperature, minimum inlet temperature) and the filter
  change interval in days.
- **Standby** — a switch that writes the unit's standby register (1 = on,
  2 = normal). The unit never acknowledges the command, so the switch is
  optimistic.

## Architecture

- `coordinator.py` polls the unit on a schedule through the connection owned by
  the core `modbus` integration; the entry reloads when that connection drops.
- The register protocol lives in the external
  [`brink-flair-modbus`](https://github.com/ysmilda/brink-flair-modbus)
  library, published to PyPI and pinned in the manifest. The integration code
  mirrors [`homeassistant/components/brink_flair` in Home Assistant
  core](https://github.com/home-assistant/core/tree/dev/homeassistant/components/brink_flair).

## Development

The component code is maintained in Home Assistant core
(`homeassistant/components/brink_flair`, with tests under
`tests/components/brink_flair`) and copied into this repository for the HACS
distribution. Home Assistant must have the `modbus` integration
available on this install for the dependency to resolve: the built-in `modbus`
integration's own requirements install `modbus-connection`, which
`brink-flair-modbus` builds on.