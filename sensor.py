"""Sensor platform for the Smarthome custom integration."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.mqtt import async_subscribe, MQTTMessage
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import DEFAULT_VALUE_TEMPLATE, DEFAULT_RELAY_DEVICE, DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """
    Set up Smarthome sensors for a module based on the config entry.

    The configuration must contain:
     - module_id: The index of the module.
     - relay_count: How many relay sensors to create.
     - value_template: (optional) Template for processing MQTT payloads.
    """
    module_id = entry.data["module_id"]
    relay_count = entry.data["relay_count"]
    value_template = entry.data.get("value_template", DEFAULT_VALUE_TEMPLATE)

    sensors = []
    for relay_index in range(relay_count):
        sensor = SmarthomeMqttSensor(hass, module_id, relay_index, value_template)
        sensors.append(sensor)
    async_add_entities(sensors)

class SmarthomeMqttSensor(SensorEntity):
    """Representation of a Smarthome MQTT sensor for a specific relay in a module."""

    def __init__(self, hass: HomeAssistant, module_id: int, relay_index: int, value_template: str) -> None:
        """Initialize the sensor for a given module and relay index."""
        self._hass = hass
        self._module_id = module_id
        self._relay_index = relay_index
        self._value_template = value_template
        self._state = None
        self._unique_id = f"smarthome.modules.{module_id}.relays.{relay_index}"
        self._state_topic = f"modules/{module_id}/relays/{relay_index}"
        self._name = f"Module {module_id} Relay {relay_index}"
        self._unsubscribe_mqtt = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to the MQTT topic when the sensor is added to Home Assistant."""
        self._unsubscribe_mqtt = await async_subscribe(
            self._hass,
            self._state_topic,
            self._message_received,
            qos=1,
        )
        _LOGGER.debug("Sensor %s subscribed to topic: %s", self._unique_id, self._state_topic)

    async def _message_received(self, msg: MQTTMessage) -> None:
        """Handle new MQTT messages and update the sensor state."""
        payload = msg.payload.decode("utf-8")
        _LOGGER.debug("Sensor %s received payload: %s", self._unique_id, payload)
        if self._value_template:
            # NOTE: Using eval for template processing is not secure.
            # Consider using Home Assistant's secure template rendering instead.
            try:
                payload = eval(self._value_template, {"value": payload})
            except Exception as err:
                _LOGGER.error("Error processing value_template for sensor %s: %s", self._unique_id, err)
        self._state = payload
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up MQTT subscription when the sensor is removed."""
        if self._unsubscribe_mqtt is not None:
            self._unsubscribe_mqtt()

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return self._unique_id

    @property
    def state(self):
        """Return the current state of the sensor."""
        return self._state

    @property
    def device_info(self):
        """Return device information for the sensor."""
        return {
            "identifiers": {(DEFAULT_RELAY_DEVICE["manufacturer"], f"modules.{self._module_id}")},
            "name": DEFAULT_RELAY_DEVICE["name"],
            "manufacturer": DEFAULT_RELAY_DEVICE["manufacturer"],
            "model": DEFAULT_RELAY_DEVICE["model"],
        }
