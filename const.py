"""Constants for the Smarthome custom integration."""

DOMAIN = "hassio_smarthome"

# Default value template for processing MQTT payloads.
DEFAULT_VALUE_TEMPLATE = "{{ value }}"

# Default device info used for all relay sensors.
DEFAULT_RELAY_DEVICE = {
    "name": "robocore-relay",
    "manufacturer": "Robocore",
    "model": "Serial Relay Module",
}
