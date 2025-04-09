"""Sensor platform for the Smarthome custom integration."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.mqtt import async_subscribe
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import DEFAULT_VALUE_TEMPLATE, DEFAULT_RELAY_DEVICE, DEFAULT_BUTTON_DEVICE, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """
    Set up Smarthome sensor entities for the module (Hub) based on the config entry.

    Expected configuration keys:
      - module_id: The index of the module.
      - relay_count: How many relay sensors to create.
      - button_count: How many button sensors to create.
      - value_template: (optional) Template for processing MQTT payloads.
    """
    module_id = entry.data["module_id"]
    relay_count = entry.data.get("relay_count", 0)
    button_count = entry.data.get("button_count", 0)
    value_template = entry.data.get("value_template", DEFAULT_VALUE_TEMPLATE)

    sensors = []
    # Create relay sensor entities.
    for relay_index in range(relay_count):
        sensor = SmarthomeMqttSensor(
            hass, module_id, relay_index, "relay", value_template)
        sensors.append(sensor)
    # Create button sensor entities.
    for button_index in range(button_count):
        sensor = SmarthomeMqttSensor(
            hass, module_id, button_index, "button", value_template)
        sensors.append(sensor)
    async_add_entities(sensors)


class SmarthomeMqttSensor(SensorEntity):
    """Representation of a Smarthome MQTT sensor for a specific device in a module (Hub)."""

    def __init__(self, hass: HomeAssistant, module_id: int, sensor_index: int, device_type: str, value_template: str) -> None:
        """
        Initialize the sensor for a given module and sensor index.

        :param hass: Home Assistant object.
        :param module_id: The ID of the module/hub.
        :param sensor_index: The index of the sensor within that type.
        :param device_type: "relay" or "button".
        :param value_template: Template for processing the MQTT payload.
        """
        self._hass = hass
        self._module_id = module_id
        self._sensor_index = sensor_index
        self._device_type = device_type  # "relay" or "button"
        self._value_template = value_template
        self._state = None

        if self._device_type == "relay":
            self._unique_id = f"smarthome.modules.{module_id}.relays.{sensor_index}"
            self._state_topic = f"modules/{module_id}/relays/{sensor_index}"
            self._name = f"Module {module_id} Relay {sensor_index}"
        else:
            self._unique_id = f"smarthome.modules.{module_id}.buttons.{sensor_index}"
            self._state_topic = f"modules/{module_id}/buttons/{sensor_index}"
            self._name = f"Module {module_id} Button {sensor_index}"

        self._unsubscribe_mqtt = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to the MQTT topic when the sensor is added to Home Assistant."""
        self._unsubscribe_mqtt = await async_subscribe(
            self._hass,
            self._state_topic,
            self._message_received,
            qos=1,
        )
        _LOGGER.debug("Sensor %s subscribed to topic: %s",
                      self._unique_id, self._state_topic)

    async def _message_received(self, msg) -> None:
        """Handle new MQTT messages and update the sensor state."""
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        _LOGGER.debug("Sensor %s received payload: %s",
                      self._unique_id, payload)
        if self._value_template:
            try:
                from homeassistant.helpers.template import Template
                tmpl = Template(self._value_template, hass=self._hass)
                # Attempt to render using async_render:
                tmpl_result = tmpl.async_render({"value": payload})
                try:
                    payload = await tmpl_result
                except TypeError:
                    # If tmpl_result is not awaitable, use the result directly.
                    payload = tmpl_result
            except Exception as err:
                _LOGGER.error(
                    "Error processing value_template for sensor %s: %s", self._unique_id, err)
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
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def state(self):
        """Return the current state of the sensor."""
        return self._state

    @property
    def device_info(self):
        """Return device information for the sensor."""
        device = DEFAULT_RELAY_DEVICE if self._device_type == "relay" else DEFAULT_BUTTON_DEVICE
        return {
            "identifiers": {(device["manufacturer"], f"modules.{self._module_id}")},
            "name": device["name"],
            "manufacturer": device["manufacturer"],
            "model": device["model"],
        }
