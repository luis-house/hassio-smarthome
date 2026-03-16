"""Sensor platform for the Smarthome custom integration (buttons only)."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_VALUE_TEMPLATE, DOMAIN
from .mqtt_mixin import SmarthomeMqttMixin

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Smarthome button sensor entities from a config entry."""
    module_id = entry.data["module_id"]
    button_count = entry.data.get("button_count", 0)
    value_template = entry.data.get("value_template", DEFAULT_VALUE_TEMPLATE)

    async_add_entities(
        SmarthomeMqttSensor(module_id, button_index, value_template)
        for button_index in range(button_count)
    )


class SmarthomeMqttSensor(SmarthomeMqttMixin, SensorEntity):
    """Representation of a Smarthome MQTT sensor for a button on a module."""

    _attr_should_poll = False

    def __init__(
        self, module_id: int, sensor_index: int, value_template: str
    ) -> None:
        self._module_id = module_id
        self._sensor_index = sensor_index

        self._attr_unique_id = f"smarthome.modules.{module_id}.buttons.{sensor_index}"
        self._attr_name = f"Module {module_id} Button {sensor_index}"
        self._attr_native_value = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"modules.{module_id}")},
            name=f"Module {module_id}",
            manufacturer="Schneider Electric",
            model="Orion",
        )

        self._setup_mqtt(
            topic=f"modules/{module_id}/buttons/{sensor_index}",
            value_template=value_template,
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to the MQTT state topic."""
        await self._subscribe_mqtt()
        _LOGGER.debug(
            "Sensor %s subscribed to topic: %s",
            self._attr_unique_id,
            self._state_topic,
        )

    async def _message_received(self, msg) -> None:
        """Handle incoming MQTT messages, update state and fire button event."""
        payload = self._render_payload(msg.payload)
        _LOGGER.debug("Sensor %s received payload: %s", self._attr_unique_id, payload)

        self._attr_native_value = payload
        self.async_write_ha_state()

        if payload == "1":
            _LOGGER.debug(
                "Sensor %s detected a button press event.", self._attr_unique_id
            )
            self.hass.bus.async_fire(
                "smarthome_button_pressed", {"entity_id": self.entity_id}
            )

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        self._unsubscribe_mqtt_handler()
