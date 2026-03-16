"""Shared MQTT mixin for Smarthome entities."""
import logging

from homeassistant.components.mqtt import async_subscribe
from homeassistant.helpers.template import Template

_LOGGER = logging.getLogger(__name__)


class SmarthomeMqttMixin:
    """Mixin providing shared MQTT subscription lifecycle and payload rendering.

    Subclasses must implement ``_message_received(self, msg)`` and call
    ``_setup_mqtt`` from their ``__init__``.  The mixin uses ``self.hass``
    (provided by the Entity base class after ``async_added_to_hass``), so
    subclasses must NOT pass ``hass`` to the constructor.
    """

    def _setup_mqtt(self, topic: str, value_template: str) -> None:
        """Store MQTT config. Call this from the entity __init__."""
        self._state_topic: str = topic
        self._value_template_str: str = value_template
        self._compiled_template: Template | None = None
        self._unsubscribe_mqtt = None

    async def _subscribe_mqtt(self) -> None:
        """Subscribe to the state topic. Call from async_added_to_hass."""
        self._unsubscribe_mqtt = await async_subscribe(
            self.hass, self._state_topic, self._message_received, qos=1
        )

    def _unsubscribe_mqtt_handler(self) -> None:
        """Unsubscribe from MQTT. Call from async_will_remove_from_hass."""
        if self._unsubscribe_mqtt is not None:
            self._unsubscribe_mqtt()

    def _render_payload(self, raw_payload) -> str:
        """Decode and optionally render a template against the raw payload.

        The Template object is compiled once and cached so that repeated MQTT
        messages do not re-parse the template string every time.
        ``async_render`` is synchronous despite its name -- no ``await`` needed.
        """
        payload = raw_payload
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")

        if self._value_template_str:
            if self._compiled_template is None:
                self._compiled_template = Template(
                    self._value_template_str, hass=self.hass
                )
            try:
                payload = self._compiled_template.async_render({"value": payload})
            except Exception as err:
                _LOGGER.error(
                    "Error rendering value_template for %s: %s",
                    getattr(self, "_attr_unique_id", repr(self)),
                    err,
                )

        return str(payload).strip()
