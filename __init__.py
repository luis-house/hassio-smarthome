"""The Smarthome Platform integration."""

from .const import DOMAIN
from homeassistant.const import Platform


PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup(hass, config):
    """Set up the integration from YAML (not used, but required)."""
    return True

async def async_setup_entry(hass, entry):
    """Set up Smarthome Platform from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    """Unload Smarthome Platform config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

async def async_migrate_entry(hass, entry):
    """Migrate config entry to a new version."""
    # Example migration logic
    # if entry.version == 1:
    #     entry.data["new_key"] = "new_value"
    #     entry.version = 2
    #     hass.config_entries.async_update_entry(entry)
    # return True 
    return True
