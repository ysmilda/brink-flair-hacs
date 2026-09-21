# Brink Flair for Home Assistant (HACS)

Custom integration for the **Brink Flair** (and compatible) ventilation units —
models 200, 225, 300, 325, 400, 450 and 600 — over Modbus.

The integration borrows a Modbus connection from the built-in `modbus`
integration and talks to the unit's register map through the
[`brink-flair-modbus`](https://github.com/ysmilda/brink-flair-modbus) Python
library (published to PyPI). Home Assistant installs it automatically from the
manifest requirements; the `modbus` and `usb` components resolve themselves.

## Installation parameters

1. Install via HACS (`Integrations` → ⋯ → *Custom repositories* → this repo, category *Integration*)
   or clone it into `<config>/custom_components/brink_flair/`.
2. Restart Home Assistant. The built-in `modbus` integration must be available
   on the install (it ships with Home Assistant), because the integration
   borrows its Modbus connection from it.
3. **On the unit** (menu 14 – Communication): `TypeBus=Modbus`, `Slave Address=20`
   (any 1–255, e.g. Viessmann Vitovent units use `70`), `Baudrate=19200`, `Parity=Even`.
   A Flair 300 needs the `TypeBus` set to Modbus and a wired setpoint; the LCD panel
   then shows `EBus` until the first Modbus write, which switches it to `Modelbus`.
4. Add *Brink Flair* via **Settings → Devices & Services**, choose Modbus TCP or
   serial, fill in the connection parameters and the unit's slave address.
   If the unit's device type (register 4004) isn't mapped yet, the flow asks
   you to pick your model — the choice is saved so the airflow limits match, and
   the step offers links to submit the found device type for the mapping.

## Configuration parameters

The config flow has a single form with the following parameters:

| Parameter | Transport | Description | Default |
|---|---|---|---|
| `type` | both | `tcp` for a Modbus TCP gateway, `serial` for a direct or proxied RS-485 link | – |
| `host` | TCP | IP address of the Modbus TCP gateway | – |
| `port` | TCP | TCP port the gateway listens on | `502` |
| `device` | serial | Serial device or networked serial proxy (`/dev/ttyUSB0`, `socket://…`) | – |
| `baudrate` | serial | Serial baud rate | `19200` |
| `unit_id` | both | The unit's Modbus station address | `20` |
| `model` | discovery | Picked manually when the device-type code is not mapped yet | detected type |

There are no config entry options and no other settings; the airflow limits of
each model are read from `brink_flair_modbus` once the model is known. The
connection settings can be changed later via **Devices & Services → configure**.

## Supported devices

Register 4004 does not report the model number; it reports an opaque
*device type* code that the integration maps to a model
(`brink_flair_modbus/device_types.py` in the library repo). Brink never
documents these codes, so the mapping holds only codes verified against real
units; unknown codes fall back to the Flair 300, so a compatible device still
works.

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

### Supported functions

- **Sensors** — supply/exhaust/outside temperature, supply/exhaust humidity,
  supply/exhaust pressure, setpoint and actual supply/exhaust volume flow,
  both fan speeds, frost heater power and fan reduction, operating mode,
  bypass and frost status, the device type, and the software/hardware
  version and serial number as diagnostics.
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

## Data updates

The coordinator reads the complete register map every 30 seconds
(`SCAN_INTERVAL`) over the connection it borrows from the core `modbus`
integration, and every entity reflects the last polled snapshot. Writes
through the *Controls* above are sent to the unit immediately, but the
corresponding entity state only flips on the next successful poll. The
standby switch is the exception: it mirrors the last request right away
because the unit never acknowledges the register.

The setpoint volume-flow sensors are registered but **disabled by default**
— they exist solely to let users assign their own sensors to the unit's
setpoints in the *Fossil fuel backup* mode; enable them from the entity
list if you want them. If the connection is lost, the entry reloads and the
entities report unavailable until a connection can be re-established.

## Examples

Scale the desired flow rate with the bedroom temperature (uses a `number`):

```yaml
alias: "Ventilation: more fresh air when it is warm"
trigger:
  - platform: numeric_state
    entity_id: sensor.flair_300_supply_temperature
    above: 24
  - platform: numeric_state
    entity_id: sensor.flair_300_supply_temperature
    below: 20
action:
  - service: number.set_value
    target:
      entity_id: number.flair_300_desired_flow_rate
    data:
      value: "{{ 250 if trigger.to_state.state < 20 else 165 }}"
```

Purge the house after cooking or painting (switch control mode + boost):

```yaml
alias: "Ventilation: purge mode while cooking"
trigger:
  - platform: state
    entity_id: binary_sensor.kitchen_smoke
    to: "on"
condition: []
action:
  - service: switch.turn_on
    target:
      entity_id: switch.flair_300_bypass_boost
  - service: select.select_option
    target:
      entity_id: select.flair_300_control_mode
    data:
      option: flow
```

Remind about the filter (the dirty flag is also a binary sensor):

```yaml
alias: "Ventilation: filter is due"
trigger:
  - platform: state
    entity_id: binary_sensor.flair_300_status_filter_dirty
    to: "on"
action:
  - service: persistent_notification.create
    data:
      title: Ventilation filter
      message: The Brink Flair filter is dirty — replace it and press reset.
```

## Known limitations

- **Standby is not acknowledged** — the unit never reads the standby register
  back, so the standby switch can disagree with the unit until a write lands.
- **Device-type mapping** — the codes in register 4004 are undocumented by
  Brink. Unknown codes fall back to the Flair 300 airflow envelope and the
  user is asked to pick the model; the mapping is updated in the library as
  new codes are verified.
- **Poll interval** — state changes written from Home Assistant appear only
  after the next 30-second poll.
- **Disabled setpoint sensors** — the volume-flow setpoint sensors ship
  disabled; enable them from the entity list when you need them.

## Use cases

- **Custom ventilation schedules** — drive the step level or desired flow
  rate from Home Assistant automations (time, presence, CO₂ or humidity
  sensors) instead of the unit's built-in timer.
- **Manual control** — take over with *Modbus Step* / *Modbus Flow* control
  mode, or switch the unit to standby (parked / holiday mode) from a dashboard.
- **Summer bypass control** — force the bypass open/closed under your own
  inside/outside temperature logic, and keep the air intake cool by raising
  the supply flow.
- **Filter lifecycle** — track remaining filter life, get a dirty-filter
  notification, and reset the counter after a replacement.
- **Fossil fuel backup** — wire the unit's setpoint sensors into the *Fossil
  fuel backup* option so the supply temperature adapts to the boiler curve.

## Troubleshooting

- **`cannot connect` / `device not found` during setup** — confirm the unit is
  powered and reachable (ping the gateway, verify the serial device exists),
  the unit's Modbus *Slave Address* matches the `unit_id` you entered, and the
  RS-485 A/B wires are not swapped. Modbus TCP gateways usually listen on
  port 502.
- **The LCD shows `EBus` instead of `Modbus`** — the unit switches to Modbus
  bus mode on the first successful register write. Set menu 14's `TypeBus`
  to Modbus and send any setting (e.g. toggle the standby switch).
- **The setup asks for a model** — the device-type code in register 4004 is
  not mapped (yet). Pick your model to proceed. The discovered code is shown
  on that step; please submit it so the mapping can be extended.
- **Entities show *unavailable*** — the Modbus connection dropped; the entry
  reloads automatically once a connection can be re-established. Check the
  network/serial link and the Home Assistant log for
  `brink_flair`-related errors.
- **A value does not change after a write** — writes take effect on the next
  poll (30 s). If it never changes, the write may have been rejected by the
  unit (e.g. the bypass override guard blocks a forced bypass above 200 m³/h
  supply flow).

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