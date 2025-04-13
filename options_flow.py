import logging
import yaml
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector  # New import for selectors

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Default YAML template shown in the options form if no mapping is set.
DEFAULT_MAPPING_YAML = """\
# Enter your button-to-relay mapping here.
# Example:
# 12: 4
# 15: [4, 5]
"""


class SmarthomeOptionsFlow(config_entries.OptionsFlow):
    """Handle Options Flow for the Smarthome integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.options = config_entry.options

    async def async_step_init(self, user_input=None):
        """Manage the options flow start."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input):
        """Handle options flow step where mapping can be edited."""
        errors = {}

        # Determine the default mapping YAML to display.
        current_mapping = self.options.get("mapping")
        if current_mapping is None:
            default_mapping = DEFAULT_MAPPING_YAML
        else:
            try:
                # Convert the current mapping dictionary to a YAML string.
                default_mapping = yaml.safe_dump(
                    current_mapping, default_flow_style=False)
            except Exception as err:
                _LOGGER.error("Error dumping mapping to YAML: %s", err)
                default_mapping = DEFAULT_MAPPING_YAML

        # Use the text selector with multiline enabled
        schema = vol.Schema({
            vol.Required("mapping", default=default_mapping):
                selector.TextSelector({
                    "multiline": True,
                    "rows": 10,  # Optional: specify a preferred number of rows
                    "placeholder": DEFAULT_MAPPING_YAML,
                    "mode": "yaml",  # Use YAML mode for better formatting
                })
        })

        if user_input is not None:
            mapping_str = user_input.get("mapping")
            try:
                mapping_data = yaml.safe_load(mapping_str)
                if not isinstance(mapping_data, dict):
                    errors["mapping"] = "Mapping must be a YAML dictionary."
            except Exception as exc:
                _LOGGER.error("Error parsing YAML mapping: %s", exc)
                errors["mapping"] = "Invalid YAML format."

            if errors:
                return self.async_show_form(
                    step_id="user", data_schema=schema, errors=errors
                )

            # If input is valid, update the options.
            return self.async_create_entry(data={"mapping": mapping_data})

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
