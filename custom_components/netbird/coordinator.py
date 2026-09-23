"""DataUpdateCoordinator for the NetBird integration."""

from __future__ import annotations

from datetime import timedelta
from typing import override

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import NetBirdApiClient, NetBirdAuthenticationError, NetBirdData, NetBirdError
from .const import DOMAIN, LOGGER, SCAN_INTERVAL

type NetBirdConfigEntry = ConfigEntry[NetBirdDataUpdateCoordinator]


class NetBirdDataUpdateCoordinator(DataUpdateCoordinator[NetBirdData]):
    """The NetBird Data Update Coordinator."""

    config_entry: NetBirdConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: NetBirdConfigEntry) -> None:
        """Initialize the NetBird coordinator."""
        session = async_get_clientsession(hass)
        self.client = NetBirdApiClient(
            session=session,
            api_url=config_entry.data[CONF_URL],
            api_key=config_entry.data[CONF_API_KEY],
        )
        self.previous_device_ids: set[str] = set()
        self._accessible_peers_cache: dict[str, int] = {}
        self._accessible_peers_initialized = False

        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    @override
    async def _async_update_data(self) -> NetBirdData:
        """Fetch peers, routes and network resources, and drop stale devices."""
        try:
            peers = await self.client.get_peers()
            routes = await self.client.get_routes()
            resources, routers = await self.client.get_routing_data()
            account = await self.client.get_account()
        except NetBirdAuthenticationError as err:
            raise ConfigEntryAuthFailed from err

        if account.peer_login_expiration_enabled:
            for peer in peers.values():
                if peer.login_expiration_enabled and peer.last_login:
                    peer.login_expires_at = peer.last_login + timedelta(
                        seconds=account.peer_login_expiration
                    )

        if not self._accessible_peers_initialized:
            try:
                self._accessible_peers_cache = (
                    await self.client.get_accessible_peers_counts(list(peers))
                )
            except NetBirdError:
                LOGGER.debug(
                    "Failed to fetch accessible peers counts, will retry next refresh",
                    exc_info=True,
                )
            else:
                self._accessible_peers_initialized = True

        for peer_id, count in self._accessible_peers_cache.items():
            if peer_id in peers:
                peers[peer_id].accessible_peers_count = count

        data = NetBirdData(
            peers=peers, routes=routes, resources=resources, routers=routers
        )

        current_device_ids = (
            {f"peer:{peer_id}" for peer_id in peers}
            | {f"route:{route_id}" for route_id in routes}
            | {f"resource:{resource_id}" for resource_id in resources}
        )

        if self.previous_device_ids:
            stale_device_ids = self.previous_device_ids - current_device_ids
            if stale_device_ids:
                self._remove_stale_devices(stale_device_ids)

        self.previous_device_ids = current_device_ids

        return data

    def _remove_stale_devices(self, stale_device_ids: set[str]) -> None:
        """Remove devices that no longer exist in NetBird."""
        device_registry = dr.async_get(self.hass)

        for device_id in stale_device_ids:
            device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
            if device:
                LOGGER.debug("Removing stale device: %s", device_id)
                device_registry.async_remove_device(device.id)
