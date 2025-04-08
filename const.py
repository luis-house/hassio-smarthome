"""Constants for the Smarthome custom integration."""

DOMAIN = "hassio_smarthome"

DEFAULT_VALUE_TEMPLATE = "{{ value }}"

DEFAULT_RELAY_DEVICE = {
    "name": "robocore-relay",
    "manufacturer": "Robocore",
    "model": "Serial Relay Module",
}

DEFAULT_BUTTON_DEVICE = {
    "name": "orion-button",
    "manufacturer": "Schneider Electric",
    "model": "Orion",
}
