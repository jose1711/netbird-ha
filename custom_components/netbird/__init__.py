"""The NetBird integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import NetBirdConfigEntry, NetBirdDataUpdateCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: NetBirdConfigEntry) -> bool:
    """Set up NetBird from a config entry."""
    coordinator = NetBirdDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: NetBirdConfigEntry) -> bool:
    """Unload a NetBird config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
