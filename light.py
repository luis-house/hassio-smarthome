"""Light platform for the Smarthome custom integration."""
import logging

from homeassistant.components.light import LightEntity
from homeassistant.components.mqtt import async_subscribe, async_publish
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.template import Template

from .const import DEFAULT_VALUE_TEMPLATE, DEFAULT_RELAY_DEVICE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """
    Set up Smarthome light entities for the module (Hub) based on the config entry.

    Expected configuration keys:
      - module_id: The ID of the module.
      - relay_count: How many relay lights to create.
      - value_template: (optional) Template for processing MQTT payloads.
    """
    module_id = entry.data["module_id"]
    relay_count = entry.data.get("relay_count", 0)
    value_template = entry.data.get("value_template", DEFAULT_VALUE_TEMPLATE)

    lights = []
    for relay_index in range(relay_count):
        light = SmarthomeMqttLight(hass, module_id, relay_index, value_template)
        lights.append(light)
    async_add_entities(lights)


class SmarthomeMqttLight(LightEntity):
    """Representation of a Smarthome MQTT light for a specific module relay."""

    def __init__(self, hass: HomeAssistant, module_id: int, relay_index: int, value_template: str) -> None:
        """
        Initialize the light for a given module and relay index.

        :param hass: Home Assistant object.
        :param module_id: The module/hub ID.
        :param relay_index: The index of the relay.
        :param value_template: Template for processing the MQTT payload.
        """
        self._hass = hass
        self._module_id = module_id
        self._relay_index = relay_index
        self._value_template = value_template  # May be empty if not used.
        self._state = False

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
        _LOGGER.debug("Light %s subscribed to topic: %s", self._unique_id, self._state_topic)

    async def _message_received(self, msg) -> None:
        """Handle incoming MQTT messages and update the light state."""
        # Convert the payload to a string regardless of type, then remove extra whitespace.
        payload = msg.payload
        _LOGGER.debug("Light %s received payload: %s", self._unique_id, payload)

        # # Process the payload with the value template if one is provided.
        # if self._value_template:
        #     try:
        #         tmpl = Template(self._value_template, hass=self._hass)
        #         tmpl_result = tmpl.async_render({"value": payload})
        #         try:
        #             payload = await tmpl_result
        #         except TypeError:
        #             payload = tmpl_result
        #         payload = str(payload).strip()
        #     except Exception as err:
        #         _LOGGER.error("Error processing value_template for light %s: %s", self._unique_id, err)

        # Interpret the MQTT payload: "1" means ON and "0" means OFF.
        if payload == 1:
            self._state = True
        elif payload == 0:
            self._state = False
        else:
            _LOGGER.error("Unexpected payload for light %s: %s", self._unique_id, payload)
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the light on by publishing '1' to the MQTT command topic.
        
        The state will update once the MQTT device publishes the new state.
        """
        await async_publish(
            self._hass,
            self._command_topic,
            "1",
            qos=1,
        )
        _LOGGER.debug("Light %s turn on command published to %s; awaiting MQTT state update", self._unique_id, self._command_topic)

    async def async_turn_off(self, **kwargs):
        """Turn the light off by publishing '0' to the MQTT command topic.
        
        The state will update once the MQTT device publishes the new state.
        """
        await async_publish(
            self._hass,
            self._command_topic,
            "0",
            qos=1,
        )
        _LOGGER.debug("Light %s turn off command published to %s; awaiting MQTT state update", self._unique_id, self._command_topic)

    async def async_will_remove_from_hass(self) -> None:
        """Clean up the MQTT subscription when the light is removed."""
        if self._unsubscribe_mqtt is not None:
            self._unsubscribe_mqtt()

    @property
    def should_poll(self) -> bool:
        """Return False since state is updated via MQTT."""
        return False

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
        """Return the supported features. No extra features are provided."""
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
