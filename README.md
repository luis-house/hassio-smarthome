# hassio-smarthome

A Home Assistant custom integration for Robocore relay modules and Schneider Electric Orion button panels, communicating over MQTT.

Each **module** (hub) exposes:
- **Relay lights** — `light.module_X_light_Y` — on/off control via MQTT publish, state updated via MQTT subscribe.
- **Button sensors** — `sensor.module_X_button_Y` — state updated on MQTT message, fires a `smarthome_button_pressed` HA event on press (payload `"1"`).

---

## Requirements

- Home Assistant 2024.1 or later
- The [MQTT integration](https://www.home-assistant.io/integrations/mqtt/) configured and connected to your broker

---

## Installation

### Manual

1. Copy the `hassio_smarthome` folder into your HA `custom_components` directory:
   ```
   <config>/custom_components/hassio_smarthome/
   ```
2. Restart Home Assistant.

### HACS (manual repository)

1. In HACS, go to **Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/luis-house/hassio-smarthome` with category **Integration**.
3. Install **Smarthome Platform** from the HACS integrations list.
4. Restart Home Assistant.

---

## Configuration

Add each module through the UI:

**Settings → Devices & Services → Add Integration → Smarthome Platform**

| Field | Description | Default |
|---|---|---|
| **Module ID** | Numeric ID matching the hardware configuration | required |
| **Number of relays** | How many relay-controlled lights this module has | 8 |
| **Number of buttons** | How many physical button inputs this module has | 8 |
| **Value template** | Jinja2 template applied to every incoming MQTT payload | `{{ value }}` |

One config entry per physical module. Modules with only relays set button count to 0, and vice versa.

---

## Options (Button-to-Relay Mapping)

After setup, click **Configure** on a module entry to set an optional button-to-relay mapping. This is a YAML dictionary where keys are button indices and values are relay indices (or a list of indices):

```yaml
0: 0          # button 0 controls relay 0
1: [0, 1]     # button 1 controls relays 0 and 1
2: 3
```

---

## MQTT Topics

All topics follow the pattern `modules/{module_id}/{type}/{index}`.

### Relay lights

| Direction | Topic | Payload |
|---|---|---|
| Subscribe (state) | `modules/{id}/relays/{idx}` | `"1"` = on, `"0"` = off |
| Publish (command) | `modules/{id}/relays/{idx}` | `"1"` = turn on, `"0"` = turn off |

State and command topics are the same. The integration publishes a command and waits for the device to echo the new state back on the same topic.

### Button sensors

| Direction | Topic | Payload |
|---|---|---|
| Subscribe (state) | `modules/{id}/buttons/{idx}` | `"1"` = pressed, `"0"` = released |

---

## Entities

### Lights

- Entity ID: `light.module_{id}_light_{idx}`
- Domain: `light`
- Device: `Module {id}` (manufacturer: Robocore, model: Serial Relay Module)
- Supported features: on/off only (`ColorMode.ONOFF`)

### Buttons

- Entity ID: `sensor.module_{id}_button_{idx}`
- Domain: `sensor`
- Device: `Module {id}` (manufacturer: Schneider Electric, model: Orion)
- State: last received payload string
- Fires HA event `smarthome_button_pressed` with `{"entity_id": "sensor.module_X_button_Y"}` when payload is `"1"`

---

## Automations

### Trigger on button press (via HA event)

```yaml
trigger:
  - platform: event
    event_type: smarthome_button_pressed
    event_data:
      entity_id: sensor.module_1_button_0
action:
  - service: light.toggle
    target:
      entity_id: light.module_1_light_0
```

### Trigger on button press (via state change)

```yaml
trigger:
  - platform: state
    entity_id: sensor.module_1_button_0
    to: "1"
```

---

## Architecture

```
MQTT Broker
    │
    ├── modules/{id}/relays/{idx}  ──▶  SmarthomeMqttLight  ──▶  light.* entity
    │                              ◀──  (publishes "1"/"0" for turn_on/turn_off)
    │
    └── modules/{id}/buttons/{idx} ──▶  SmarthomeMqttSensor ──▶  sensor.* entity
                                                              ──▶  smarthome_button_pressed event
```

Both entity types share `SmarthomeMqttMixin` for MQTT subscription lifecycle and Jinja2 template rendering.

---

## Future Plans

See [MIGRATION.md](MIGRATION.md) for the planned migration of button entities from `SensorEntity` to `EventEntity`, which will improve native automation support.

---

## Development

```
hassio_smarthome/
├── __init__.py        # Integration setup / teardown
├── manifest.json      # Integration metadata
├── const.py           # DOMAIN and default constants
├── config_flow.py     # UI config flow
├── options_flow.py    # UI options flow (button-to-relay mapping)
├── mqtt_mixin.py      # Shared MQTT subscribe/template mixin
├── light.py           # Relay light platform
├── sensor.py          # Button sensor platform
└── strings.json       # Localization strings
```
