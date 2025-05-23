"""Sensor platform for the Smarthome custom integration (buttons only)."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.mqtt import async_subscribe
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import DEFAULT_VALUE_TEMPLATE, DEFAULT_BUTTON_DEVICE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """
    Set up Smarthome sensor entities for the module (Hub) based on the config entry.

    This platform now creates only button sensor entities.

    Expected configuration keys:
      - module_id: The index of the module.
      - button_count: How many button sensors to create.
      - value_template: (optional) Template for processing MQTT payloads.
    """
    module_id = entry.data["module_id"]
    button_count = entry.data.get("button_count", 0)
    value_template = entry.data.get("value_template", DEFAULT_VALUE_TEMPLATE)

    sensors = []
    # Create button sensor entities.
    for button_index in range(button_count):
        sensor = SmarthomeMqttSensor(hass, module_id, button_index, value_template)
        sensors.append(sensor)
    async_add_entities(sensors)


class SmarthomeMqttSensor(SensorEntity):
    """Representation of a Smarthome MQTT sensor for a button on a module (Hub)."""

    def __init__(self, hass: HomeAssistant, module_id: int, sensor_index: int, value_template: str) -> None:
        """
        Initialize the sensor for a given module and button index.

        :param hass: Home Assistant object.
        :param module_id: The ID of the module/hub.
        :param sensor_index: The index of the button sensor.
        :param value_template: Template for processing MQTT payloads.
        """
        self._hass = hass
        self._module_id = module_id
        self._sensor_index = sensor_index
        self._value_template = value_template
        self._state = None

        # Setup identifiers and topics specific to buttons.
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
        _LOGGER.debug("Sensor %s subscribed to topic: %s", self._unique_id, self._state_topic)

    async def _message_received(self, msg) -> None:
        """Handle new MQTT messages, update the sensor state, and fire a device trigger event on button press."""
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        _LOGGER.debug("Sensor %s received payload: %s", self._unique_id, payload)
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
                _LOGGER.error("Error processing value_template for sensor %s: %s", self._unique_id, err)
        self._state = payload
        self.async_write_ha_state()

        # Fire a custom event if the payload indicates the button was pressed.
        if payload == 1:
            _LOGGER.debug("Sensor %s detected a button press event.", self._unique_id)
            # Fire event with entity_id so that device triggers can reference this sensor.
            self._hass.bus.async_fire("smarthome_button_pressed", {"entity_id": self.entity_id})

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
        device = DEFAULT_BUTTON_DEVICE
        return {
            "identifiers": {(device["manufacturer"], f"modules.{self._module_id}")},
            "name": device["name"],
            "manufacturer": device["manufacturer"],
            "model": device["model"],
        }
