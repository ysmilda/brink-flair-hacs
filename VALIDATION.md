# Live validation plan

Validating this integration against a real Brink Flair unit before trusting it
with writes. All values below map 1:1 to the register map documented in the
integration (`brink_flair_modbus/subsystems/*`) and to the reference ESPHome
config `fonske/Brink-flair-modbus`.

## Topology

The integration connects as a **Modbus TCP master**. The unit only speaks
RS-485, so the physical link must be a serial-to-TCP gateway:

- An RS485-Ethernet converter (server listening on TCP), the unit on its
  RS-485 port; or
- an ESP32 flashed so its Modbus link is reachable over TCP (the reference
  ESPHome project runs the ESP as *modbus master* and publishes ESPHome API
  entities instead — that path uses the ESPHome integration, not this one; the
  two can run side by side to cross-check register values).

The reference project also documents the unit-side settings:

- Menu 14 – Communication: `TypeBus=Modbus`, `Slave Address=20` (any 1–255;
  Viessmann Vitovent uses `70`), `Baudrate=19200`, `Parity=Even`.
- After power-up the unit stays on the LCD/eBus mode until the first Modbus
  write; the reference config writes control mode `1` (Modbus Step) on boot.

## Pre-flight

1. Confirm the gateway answers: read register `4004` and expect the device
   type (200/225/300/325/400/450/600). For a Flair 300:
   `pymodbus` or `modpoll -r 4004 -c 1 -0 -1 20 <gw>` should print `300`.
2. In Home Assistant, **Settings → Devices & Services → Add Integration →
   Brink Flair** → Modbus TCP → gateway address/port, slave address 20.
3. The created device should show `Brink Flair 300` (manufacturer *Brink*).

## Read-back check (values for a Flair 300)

| Register | Entity | Raw example | Decoded |
|---:|---|---:|---:|
| 4004 | (device) | 300 | model 300 |
| 4020 | sensor.…_operating_mode | 12 | `auto_modbus` |
| 4032 | sensor.…_supply_volume_flow | 149 | 149 m³/h |
| 4036 | sensor.…_supply_temperature | 215 | 21.5 °C |
| 4037 | sensor.…_supply_humidity | 45 | 45 % |
| 4044 | sensor.…_exhaust_fan_speed | 890 | 890 RPM |
| 4050 | sensor.…_bypass_status | 4 | `closed` |
| 4070 | sensor.…_frost_status | 2 | `no_frost` |
| 4100 | binary_sensor.…_filter_dirty | 0 | `off` |
| 4115 | sensor.…_filter_hours_used | 240 | 10 days |
| 4116/4117 | sensor.…_filter_used_volume | 0/500 | 500 m³ |
| 8000 | select.…_control_mode | 1 | `step` |
| 8001 | select.…_level | 2 | `medium` |
| 8002 | number.…_desired_flow_rate | 140 | 140 m³/h |
| 6000–6003 | number.…_flow_rate_step_0..3 | 100–180 | 100–180 m³/h |
| 6035/6036 | number.…_intake/exhaust_imbalance | 0 | 0 % |
| 6100 | select.…_bypass_mode | 0 | `auto` |
| 6101 | number.…_bypass_temperature_inside | 240 | 24.0 °C |
| 6102 | number.…_bypass_temperature_outside | 100 | 10.0 °C |
| 6103 | number.…_bypass_hysteresis | 20 | 2.0 °C |
| 6104 | switch.…_bypass_boost | 0 | `off` |
| 6105 | number.…_bypass_boost_position | 3 | step 3 |
| 6110 | number.…_frost_control_temperature | 0 | 0.0 °C |
| 6111 | number.…_frost_minimum_inlet_temperature | 100 | 10.0 °C |

Compare the sensor values against the physical unit (LCD) and, when available,
against the ESPHome API entities reading the same registers.

## Write tests (do these in a controlled order)

1. **Control mode** → select `modbus_step`. The unit LCD switches from the
   eBus/panel control to Modbus. Register `8000` reads back `1`.
2. **Level** → select `low`/`medium`. Fan speed registers (`4034`, `4044`)
   step down/up and the audible airflow changes.
3. **Flow step numbers** → set `flow_rate_step_0` to a value below `flow_max`
   (`300` for a Flair 300; `50` lower bound for steps 1–3). Boundary check:
   `47` must be rejected by the UI (`native_min_value=50`).
4. **Flow mode** → set control mode to `modbus_flow`, then set
   `desired_flow_rate` (0–280 for a Flair 300, 0–600 for a 600). The supply
   volume (`4032`) should converge on the target.
5. **Bypass override** → with supply volume (`4032`) above 200 m³/h, setting
   `select.…_bypass_mode` to `closed`/`open` must fail with "Bypass override
   blocked…" and register `6100` must stay `0`. Repeat below 200 m³/h — the
   write goes through and the register reads back the chosen value.
6. **Bypass / frost numbers** → set `bypass_temperature_inside` to `24.5`;
   register `6101` reads back `245`. Same write/read-back for `6102`–`6103` and
   `6110`–`6111` (tenths of a degree, step 0.5) and `6035`/`6036` (tenths of a
   percent, whole-percent step).
7. **Bypass boost** → `switch.…_bypass_boost` `on` sets bit 0 of `6104`;
   it reads back `1` (and `0` when `off`). `number.…_bypass_boost_position`
   bounds are `0`–`3`.
8. **Standby** → `switch.…_standby` `on`/`off` writes `1`/`2` to register
   `8003`. Per the reference config this register is not read back, so the
   switch reports the last command (optimistic) — confirm the unit actually
   enters and leaves standby on the LCD.
9. **Filter reset** → press `button.…_filter_reset`. Register `8010` pulses
   `1 → 0`, and `4115` (`filter_hours_used`) resets to ~0.
10. **Invalid write** → write `desired_flow_rate=1000` from the developer
    tools; the library rejects it (no register write) and the entity keeps its
    old value.

## Edge cases

- **Absent sensors**: unread values are reported as `unknown` (register
  `0x7FFF`, `NAN_INT16`), not `0`. Confirm e.g. the frost sensor when room
  temperature is above the frost threshold.
- **Big models**: repea the model read-back with a 400/450/600 if one is
  available; `desired_flow_rate` max becomes 400/450/600.
- **Connection drop**: unplug the serial cable; the `modbus` integration
  drops the shared connection and the entry reloads automatically
  (`async_schedule_reload`), re-borrowing a unit. Logs under
  `homeassistant.components.modbus` and `homeassistant.components.brink_flair`.

## Sign-off

Document the model, firmware menu-14 values, and the observed read-back table
for the record, and only then let automations write to the unit.