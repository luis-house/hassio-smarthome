"""Config flow for the Smarthome custom integration."""
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries

from .const import DOMAIN, DEFAULT_VALUE_TEMPLATE

DATA_SCHEMA = vol.Schema({
    vol.Required("module_id"): vol.Coerce(int),
    vol.Required("relay_count", default=8): vol.Coerce(int),
    vol.Optional("value_template", default=DEFAULT_VALUE_TEMPLATE): cv.string,
})

class SmarthomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Smarthome integration."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step of the config flow."""
        errors = {}
        if user_input is not None:
            try:
                module_id = int(user_input["module_id"])
                relay_count = int(user_input["relay_count"])
                if module_id < 0:
                    errors["module_id"] = "Module ID must be non-negative."
                if relay_count <= 0:
                    errors["relay_count"] = "Relay count must be a positive integer."
            except Exception:
                errors["base"] = "Invalid input. Please check your entries."
            if not errors:
                return self.async_create_entry(
                    title=f"Module {user_input['module_id']}",
                    data=user_input,
                )
        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )
