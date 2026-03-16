# Changelog

All notable changes to this project will be documented in this file.

---

## [0.1.1] — 2026-03-16

### Fixed

- **Light entity fails to load on HA 2026.x** — `supported_color_modes` was not declared, causing `HomeAssistantError: does not set supported color modes`. Added `ColorMode.ONOFF` as required by the new HA light platform contract.
- **Light `supported_features` type error** — returning a bare `int` (`0`) instead of a `LightEntityFeature` flag caused `TypeError: argument of type 'int' is not a container or iterable` in HA 2026.x. Removed the override; the base class default is now used.
- **Button press event never fired** — `sensor.py` compared the MQTT payload (a `str`) to the integer `1`, which is always `False`. Fixed to compare against `"1"`.
- **Dead `await` on template rendering** — `Template.async_render()` is synchronous and never returns a coroutine. The `try: await ...; except TypeError:` pattern masked real errors and was removed.
- **Template object recreated on every MQTT message** — both entities re-instantiated a `Template` object for every incoming message. The compiled template is now cached after first use.
- **`OptionsFlow` constructor received `config_entry`** — passing `config_entry` to `OptionsFlow.__init__` was deprecated in HA 2024.11 and removed in HA 2025.12. The constructor argument has been removed; `self.config_entry` (provided by the base class) is used instead.
- **`SensorEntity.state` property overridden** — `state` is marked `@final` in `SensorEntity`. Changed to `native_value` as required.
- **`iot_class` incorrectly set to `local_polling`** — the integration subscribes to MQTT topics and never polls devices. Corrected to `local_push`.
- **Missing `mqtt` dependency in `manifest.json`** — both platforms import from `homeassistant.components.mqtt` but `mqtt` was not declared as a dependency, risking load-order race conditions on startup.

### Changed

- **`SmarthomeMqttMixin` extracted** (`mqtt_mixin.py`, new) — shared MQTT subscription lifecycle (subscribe, unsubscribe) and payload rendering (bytes decode + Jinja2 template) are now in a single mixin used by both `SmarthomeMqttLight` and `SmarthomeMqttSensor`. Eliminates duplicated code.
- **Modern `_attr_` entity pattern** — both entity classes now use `_attr_unique_id`, `_attr_name`, `_attr_is_on`, `_attr_native_value`, `_attr_should_poll`, `_attr_color_mode`, `_attr_supported_color_modes`, and `_attr_device_info` instead of `@property` overrides. `self._hass` is no longer stored in constructors; `self.hass` (provided by the HA `Entity` base after `async_added_to_hass`) is used instead.
- **`DeviceInfo` typed object** — `device_info` now returns a typed `DeviceInfo` instance (from `homeassistant.helpers.device_registry`) instead of a plain `dict`. Device identifiers follow the HA convention of `(DOMAIN, identifier)` instead of `(manufacturer, identifier)`.
- **`__init__.py` cleaned up** — removed the unused `async_setup(hass, config)` function (unnecessary for config-entry-only integrations) and the empty `hass.data` book-keeping that stored nothing.
- **`const.py` cleaned up** — removed `DEFAULT_RELAY_DEVICE` and `DEFAULT_BUTTON_DEVICE` dictionaries; device metadata now lives directly in `DeviceInfo` objects inside each entity.
- **Config and options flow error keys** — error values in `config_flow.py` and `options_flow.py` changed from raw English strings to translation keys (`"invalid_module_id"`, `"no_entities"`, `"invalid_yaml"`, etc.) that resolve through `strings.json`.

### Added

- **`strings.json`** — localization file for the config flow and options flow, providing human-readable field labels, descriptions, and error messages.
- **`MIGRATION.md`** — documents the deferred migration of button entities from `SensorEntity` (`sensor.*`) to `EventEntity` (`event.*`). Covers two approaches (coexist and replace), with code sketches, tradeoffs, and an automation impact checklist for future contributors.
- **`README.md`** — rewritten from a single-line stub to full documentation covering installation (manual and HACS), configuration, MQTT topic reference, entity listing, automation examples, architecture overview, and file structure.

### Not changed (backward compatibility)

- `unique_id` values for all entities are unchanged — entity registry entries remain stable.
- Entity friendly names are unchanged — `has_entity_name` not enabled in this release.
- `sensor.*` entity IDs for buttons — no platform migration in this release.
- `light.*` entity IDs for relays.
- MQTT topic structure (`modules/{id}/relays/{idx}`, `modules/{id}/buttons/{idx}`).
- Config entry schema — `VERSION` stays at `1`.
- `smarthome_button_pressed` HA bus event — continues to fire on button press; existing automations using it are unaffected.

---

## [0.1.0] — 2024-01-01

- Light entity for relay-controlled lights over MQTT (`light.*`).
- Sensor entity for physical button inputs over MQTT (`sensor.*`), firing `smarthome_button_pressed` HA events.
- Config flow for adding modules (module ID, relay count, button count, value template).
- Options flow for configuring button-to-relay mapping (YAML).
