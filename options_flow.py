"""Options flow for the Smarthome custom integration."""
import logging
import yaml
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_MAPPING_YAML = """\
# Enter your button-to-relay mapping here.
# Example:
# 0: 0
# 1: [0, 1]
"""


class SmarthomeOptionsFlow(config_entries.OptionsFlow):
    """Handle the options flow for the Smarthome integration."""

    async def async_step_init(self, user_input=None):
        """Delegate to the user step."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Handle the options step where the button-to-relay mapping is edited."""
        errors = {}

        current_mapping = self.config_entry.options.get("mapping")
        if current_mapping is None:
            default_mapping = DEFAULT_MAPPING_YAML
        else:
            try:
                default_mapping = yaml.safe_dump(current_mapping, default_flow_style=False)
            except Exception as err:
                _LOGGER.error("Error serialising mapping to YAML: %s", err)
                default_mapping = DEFAULT_MAPPING_YAML

        schema = vol.Schema({
            vol.Required("mapping", default=default_mapping): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT, multiline=True)
            )
        })

        if user_input is not None:
            mapping_str = user_input.get("mapping", "")
            try:
                mapping_data = yaml.safe_load(mapping_str)
                if not isinstance(mapping_data, dict):
                    errors["mapping"] = "not_a_dict"
            except Exception as exc:
                _LOGGER.error("Error parsing YAML mapping: %s", exc)
                errors["mapping"] = "invalid_yaml"

            if not errors:
                return self.async_create_entry(data={"mapping": mapping_data})

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
