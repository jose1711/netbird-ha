"""Diagnostics support for NetBird."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from .coordinator import NetBirdConfigEntry

TO_REDACT = {
    CONF_API_KEY,
    "id",
    "name",
    "hostname",
    "ip",
    "address",
    "network",
    "domains",
    "user_id",
    "peer",
    "peer_groups",
    "raw",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: NetBirdConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = entry.runtime_data.data
    return async_redact_data(
        {
            "peers": [asdict(peer) for peer in data.peers.values()],
            "routes": [asdict(route) for route in data.routes.values()],
            "resources": [asdict(resource) for resource in data.resources.values()],
            "routers": {
                network_id: [asdict(router) for router in routers]
                for network_id, routers in data.routers.items()
            },
        },
        TO_REDACT,
    )
