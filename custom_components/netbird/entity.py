"""Base entities for the NetBird integration."""

from __future__ import annotations

from typing import override

from homeassistant.const import CONF_URL
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import NetBirdNetworkResource, NetBirdPeer, NetBirdRoute
from .const import DEFAULT_API_URL, DOMAIN
from .coordinator import NetBirdDataUpdateCoordinator

CLOUD_PEERS_URL = "https://app.netbird.io/peers"
CLOUD_ROUTES_URL = "https://app.netbird.io/routes"
CLOUD_NETWORKS_URL = "https://app.netbird.io/networks"


class _NetBirdBaseEntity(CoordinatorEntity[NetBirdDataUpdateCoordinator]):
    """Shared behaviour for all NetBird entities."""

    _attr_has_entity_name = True

    def _cloud_configuration_url(self, url: str) -> str | None:
        """Return a dashboard link, only when using NetBird's cloud API."""
        if self.coordinator.config_entry.data.get(CONF_URL) == DEFAULT_API_URL:
            return url
        return None


class NetBirdPeerEntity(_NetBirdBaseEntity):
    """Defines a NetBird peer entity."""

    def __init__(
        self,
        *,
        coordinator: NetBirdDataUpdateCoordinator,
        peer: NetBirdPeer,
        description: EntityDescription,
    ) -> None:
        """Initialize a NetBird peer entity."""
        super().__init__(coordinator=coordinator)
        self.entity_description = description
        self.peer_id = peer.id
        self._attr_unique_id = f"peer_{peer.id}_{description.key}"

    @property
    @override
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        peer = self.coordinator.data.peers[self.peer_id]

        return DeviceInfo(
            configuration_url=self._cloud_configuration_url(CLOUD_PEERS_URL),
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"peer:{peer.id}")},
            manufacturer="NetBird",
            model=peer.os,
            name=peer.name or peer.hostname,
            sw_version=peer.version,
        )


class NetBirdRouteEntity(_NetBirdBaseEntity):
    """Defines a NetBird route entity."""

    def __init__(
        self,
        *,
        coordinator: NetBirdDataUpdateCoordinator,
        route: NetBirdRoute,
        description: EntityDescription,
    ) -> None:
        """Initialize a NetBird route entity."""
        super().__init__(coordinator=coordinator)
        self.entity_description = description
        self.route_id = route.id
        self._attr_unique_id = f"route_{route.id}_{description.key}"

    @property
    @override
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        route = self.coordinator.data.routes[self.route_id]

        return DeviceInfo(
            configuration_url=self._cloud_configuration_url(CLOUD_ROUTES_URL),
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"route:{route.id}")},
            manufacturer="NetBird",
            model="Network route",
            name=route.description or route.network_id or route.destination,
        )


class NetBirdResourceEntity(_NetBirdBaseEntity):
    """Defines a NetBird network resource entity."""

    def __init__(
        self,
        *,
        coordinator: NetBirdDataUpdateCoordinator,
        resource: NetBirdNetworkResource,
        description: EntityDescription,
    ) -> None:
        """Initialize a NetBird resource entity."""
        super().__init__(coordinator=coordinator)
        self.entity_description = description
        self.resource_id = resource.id
        self._attr_unique_id = f"resource_{resource.id}_{description.key}"

    @property
    @override
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        resource = self.coordinator.data.resources[self.resource_id]

        return DeviceInfo(
            configuration_url=self._cloud_configuration_url(CLOUD_NETWORKS_URL),
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"resource:{resource.id}")},
            manufacturer="NetBird",
            model=resource.type,
            name=resource.name,
        )
