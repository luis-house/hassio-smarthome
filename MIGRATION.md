# Migration Guide

This document tracks deferred breaking changes that are intentionally postponed to preserve backward compatibility with existing automations and entity registries.

---

## Pending: Button `sensor.*` entities → `event.*` entities

### Background

Button inputs are currently exposed as `sensor.module_X_button_Y` entities via `SensorEntity`. This is a legacy pattern: a sensor stores a raw payload string as its state and fires a custom `smarthome_button_pressed` bus event on press.

Since Home Assistant 2023.8, the proper platform for momentary actions (button presses, doorbell rings, remote controls) is `EventEntity` under the `event` domain. Event entities are stateless, purpose-built for signals, and integrate natively with the HA automation UI without requiring knowledge of custom event names.

### Why it was deferred

Migrating from `Platform.SENSOR` to `Platform.EVENT` changes every button entity ID from `sensor.module_X_button_Y` to `event.module_X_button_Y`. Any automation referencing those entities by ID would break silently.

---

### Approach A — Coexist (Recommended, non-breaking)

Run both `sensor` and `event` platforms simultaneously for a transition period.

**Step 1.** Add `Platform.EVENT` to `PLATFORMS` in `__init__.py` alongside the existing `Platform.SENSOR`.

**Step 2.** Create `event.py` with `SmarthomeMqttEventButton` using `EventEntity`:

```python
from homeassistant.components.event import EventEntity, EventDeviceClass
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DEFAULT_VALUE_TEMPLATE, DOMAIN
from .mqtt_mixin import SmarthomeMqttMixin

class SmarthomeMqttEventButton(SmarthomeMqttMixin, EventEntity):
    _attr_should_poll = False
    _attr_device_class = EventDeviceClass.BUTTON
    _attr_event_types = ["press"]

    def __init__(self, module_id: int, button_index: int, value_template: str) -> None:
        self._attr_unique_id = f"smarthome.modules.{module_id}.events.{button_index}"
        self._attr_name = f"Module {module_id} Button {button_index} Event"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"modules.{module_id}")},
            name=f"Module {module_id}",
            manufacturer="Schneider Electric",
            model="Orion",
        )
        self._setup_mqtt(
            topic=f"modules/{module_id}/buttons/{button_index}",
            value_template=value_template,
        )

    async def async_added_to_hass(self) -> None:
        await self._subscribe_mqtt()

    async def _message_received(self, msg) -> None:
        payload = self._render_payload(msg.payload)
        if payload == "1":
            self._trigger_event("press")

    async def async_will_remove_from_hass(self) -> None:
        self._unsubscribe_mqtt_handler()
```

**Step 3.** Add a deprecation log warning in `sensor.py`'s `async_added_to_hass`:

```python
import warnings
_LOGGER.warning(
    "Entity %s is deprecated. Migrate automations to the equivalent event.* entity "
    "and remove sensor entries from the entity registry.",
    self._attr_unique_id,
)
```

**Step 4.** After a suitable deprecation window (one or two releases), remove `sensor.py` and `Platform.SENSOR` from `__init__.py`.

**Tradeoffs:**
- Non-breaking: existing `sensor.*` automations continue to work.
- Users must manually remove old sensor entities from the HA entity registry and update automations.
- Temporarily creates duplicate subscriptions to the same MQTT topics (two entities per button).

---

### Approach B — Replace (Breaking, cleaner)

Replace `sensor.py` with `event.py` directly, removing `Platform.SENSOR` from `__init__.py`.

**Changes required:**

1. Rename `sensor.py` to `event.py`.
2. Change `Platform.SENSOR` → `Platform.EVENT` in `PLATFORMS` (`__init__.py`).
3. Inherit from `EventEntity` instead of `SensorEntity`.
4. Replace `self._attr_native_value = payload` + `async_write_ha_state()` with `self._trigger_event("press")`.
5. Remove the `hass.bus.async_fire("smarthome_button_pressed", ...)` call (EventEntity handles this natively through the automation UI).
6. Set `_attr_device_class = EventDeviceClass.BUTTON` and `_attr_event_types = ["press"]`.
7. Bump the integration `VERSION` in `manifest.json` and add a `async_migrate_entry` step that removes orphaned sensor entities from the entity registry.

**Tradeoffs:**
- All existing `sensor.*` automations break immediately.
- Entity registry entries for old `sensor.*` entities become orphaned (HA will clean them up eventually, or the migration step can remove them proactively).
- Cleanest long-term architecture.

---

### Automation impact checklist (both approaches)

Before removing the sensor platform, users should:

- [ ] Search HA automations for `sensor.module_*_button_*` entity references and update them to `event.module_*_button_*` (Approach A) or to use the new EventEntity trigger in the automation editor.
- [ ] Search scripts for `smarthome_button_pressed` event triggers and assess whether the native EventEntity trigger is a suitable replacement.
- [ ] Remove deprecated `sensor.module_*_button_*` entities from **Settings → Entities** after migrating.
- [ ] Remove deprecated devices if they become empty after sensor entities are removed.
