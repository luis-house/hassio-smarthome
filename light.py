"""Light platform for the Smarthome custom integration."""
import logging

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.components.mqtt import async_publish
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
    """Set up Smarthome light entities from a config entry."""
    module_id = entry.data["module_id"]
    relay_count = entry.data.get("relay_count", 0)
    value_template = entry.data.get("value_template", DEFAULT_VALUE_TEMPLATE)

    async_add_entities(
        SmarthomeMqttLight(module_id, relay_index, value_template)
        for relay_index in range(relay_count)
    )


class SmarthomeMqttLight(SmarthomeMqttMixin, LightEntity):
    """Representation of a Smarthome MQTT light for a specific module relay."""

    _attr_should_poll = False
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(
        self, module_id: int, relay_index: int, value_template: str
    ) -> None:
        self._module_id = module_id
        self._relay_index = relay_index

        self._attr_unique_id = f"smarthome.modules.{module_id}.lights.{relay_index}"
        self._attr_name = f"Module {module_id} Light {relay_index}"
        self._attr_is_on = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"modules.{module_id}")},
            name=f"Module {module_id}",
            manufacturer="Robocore",
            model="Serial Relay Module",
        )

        self._setup_mqtt(
            topic=f"modules/{module_id}/relays/{relay_index}",
            value_template=value_template,
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to the MQTT state topic."""
        await self._subscribe_mqtt()
        _LOGGER.debug(
            "Light %s subscribed to topic: %s",
            self._attr_unique_id,
            self._state_topic,
        )

    async def _message_received(self, msg) -> None:
        """Handle incoming MQTT messages and update the light state."""
        payload = self._render_payload(msg.payload)
        _LOGGER.debug("Light %s received payload: %s", self._attr_unique_id, payload)

        if payload == "1":
            self._attr_is_on = True
        elif payload == "0":
            self._attr_is_on = False
        else:
            _LOGGER.error(
                "Unexpected payload for light %s: %s", self._attr_unique_id, payload
            )
            return

        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the light by publishing to the MQTT command topic."""
        await async_publish(self.hass, self._state_topic, "1", qos=1)
        _LOGGER.debug("Published turn on command to %s", self._state_topic)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the light by publishing to the MQTT command topic."""
        await async_publish(self.hass, self._state_topic, "0", qos=1)
        _LOGGER.debug("Published turn off command to %s", self._state_topic)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from MQTT when removed."""
        self._unsubscribe_mqtt_handler()
