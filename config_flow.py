"""Config flow for the Smarthome custom integration."""
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, DEFAULT_VALUE_TEMPLATE

DATA_SCHEMA = vol.Schema({
    vol.Required("module_id"): vol.Coerce(int),
    # Specify counts independently – one Hub (module) can have a number of relays and/or buttons.
    vol.Optional("relay_count", default=8): vol.Coerce(int),
    vol.Optional("button_count", default=8): vol.Coerce(int),
    vol.Optional("value_template", default=DEFAULT_VALUE_TEMPLATE): cv.string,
})


class SmarthomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Smarthome integration."""
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow for the hassio_smarthome integration."""
        from .options_flow import SmarthomeOptionsFlow
        return SmarthomeOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step of the config flow."""
        errors = {}
        if user_input is not None:
            try:
                module_id = int(user_input["module_id"])
                relay_count = int(user_input.get("relay_count", 0))
                button_count = int(user_input.get("button_count", 0))
                if module_id < 0:
                    errors["module_id"] = "Module ID must be non-negative."
                if relay_count < 0:
                    errors["relay_count"] = "Relay count cannot be negative."
                if button_count < 0:
                    errors["button_count"] = "Button count cannot be negative."
                if relay_count == 0 and button_count == 0:
                    errors["base"] = "At least one of relay_count or button_count must be greater than 0."
            except Exception:
                errors["base"] = "Invalid input. Please check your entries."
            if not errors:
                title = (
                    f"Module {user_input['module_id']} "
                    f"(Relays: {relay_count}, Buttons: {button_count})"
                )
                return self.async_create_entry(
                    title=title,
                    data=user_input,
                )
        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )
