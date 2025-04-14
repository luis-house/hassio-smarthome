"""Light platform for the Smarthome custom integration."""
import logging

from homeassistant.components.light import LightEntity
from homeassistant.components.mqtt import async_subscribe, async_publish
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import DEFAULT_VALUE_TEMPLATE, DEFAULT_RELAY_DEVICE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """
    Set up Smarthome light entities for the module (Hub) based on the config entry.

    Expected configuration keys:
      - module_id: The index of the module.
      - relay_count: How many relay lights to create.
      - value_template: (optional) Template for processing MQTT payloads.
    """
    module_id = entry.data["module_id"]
    relay_count = entry.data.get("relay_count", 0)
    value_template = entry.data.get("value_template", DEFAULT_VALUE_TEMPLATE)

    lights = []
    # Create relay light entities.
    for relay_index in range(relay_count):
        light = SmarthomeMqttLight(
            hass, module_id, relay_index, value_template)
        lights.append(light)
    async_add_entities(lights)


class SmarthomeMqttLight(LightEntity):
    """Representation of a Smarthome MQTT light for a specific module relay."""

    def __init__(self, hass: HomeAssistant, module_id: int, relay_index: int, value_template: str) -> None:
        """
        Initialize the light for a given module and relay index.

        :param hass: Home Assistant object.
        :param module_id: The ID of the module/hub.
        :param relay_index: The index of the relay.
        :param value_template: Template for processing the MQTT payload.
        """
        self._hass = hass
        self._module_id = module_id
        self._relay_index = relay_index
        self._value_template = value_template
        self._state = None

        self._unique_id = f"smarthome.modules.{module_id}.lights.{relay_index}"
        self._state_topic = f"modules/{module_id}/relays/{relay_index}"
        self._command_topic = f"modules/{module_id}/relays/{relay_index}/set"
        self._name = f"Module {module_id} Light {relay_index}"

        self._unsubscribe_mqtt = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to the MQTT state topic when the light is added to Home Assistant."""
        self._unsubscribe_mqtt = await async_subscribe(
            self._hass,
            self._state_topic,
            self._message_received,
            qos=1,
        )
        _LOGGER.debug("Light %s subscribed to topic: %s",
                      self._unique_id, self._state_topic)

    async def _message_received(self, msg) -> None:
        """Handle incoming MQTT messages and update the light state."""
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        _LOGGER.debug("Light %s received payload: %s",
                      self._unique_id, payload)
        if self._value_template:
            try:
                from homeassistant.helpers.template import Template
                tmpl = Template(self._value_template, hass=self._hass)
                tmpl_result = tmpl.async_render({"value": payload})
                try:
                    payload = await tmpl_result
                except TypeError:
                    payload = tmpl_result
            except Exception as err:
                _LOGGER.error(
                    "Error processing value_template for light %s: %s", self._unique_id, err)
        # Update the internal state based on the payload.
        # Here we assume that payloads like "ON", "on", "true" (or equivalent) mean the light is on.
        self._state = payload.lower() in ["on", "true", "1"]
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the light on by publishing to the MQTT command topic."""
        await async_publish(
            self._hass,
            self._command_topic,
            "ON",
            qos=1,
        )
        self._state = True
        self.async_write_ha_state()
        _LOGGER.debug("Light %s turned on, published to %s",
                      self._unique_id, self._command_topic)

    async def async_turn_off(self, **kwargs):
        """Turn the light off by publishing to the MQTT command topic."""
        await async_publish(
            self._hass,
            self._command_topic,
            "OFF",
            qos=1,
        )
        self._state = False
        self.async_write_ha_state()
        _LOGGER.debug("Light %s turned off, published to %s",
                      self._unique_id, self._command_topic)

    async def async_will_remove_from_hass(self) -> None:
        """Clean up the MQTT subscription when the light is removed."""
        if self._unsubscribe_mqtt is not None:
            self._unsubscribe_mqtt()

    @property
    def name(self) -> str:
        """Return the name of the light."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the light."""
        return self._unique_id

    @property
    def is_on(self) -> bool:
        """Return True if the light is on."""
        return self._state

    @property
    def supported_features(self) -> int:
        """Return the supported features. For now, no extra features are provided."""
        return 0

    @property
    def device_info(self):
        """Return device information for the light."""
        device = DEFAULT_RELAY_DEVICE
        return {
            "identifiers": {(device["manufacturer"], f"modules.{self._module_id}")},
            "name": device["name"],
            "manufacturer": device["manufacturer"],
            "model": device["model"],
        }
