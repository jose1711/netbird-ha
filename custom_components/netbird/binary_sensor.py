"""Support for NetBird binary sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import NetBirdData, NetBirdNetworkResource, NetBirdPeer, NetBirdRoute
from .coordinator import NetBirdConfigEntry
from .entity import NetBirdPeerEntity, NetBirdResourceEntity, NetBirdRouteEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class NetBirdPeerBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a NetBird peer binary sensor entity."""

    is_on_fn: Callable[[NetBirdPeer], bool | None]


PEER_BINARY_SENSORS: tuple[NetBirdPeerBinarySensorEntityDescription, ...] = (
    NetBirdPeerBinarySensorEntityDescription(
        key="connected",
        translation_key="connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=lambda peer: peer.connected,
    ),
    NetBirdPeerBinarySensorEntityDescription(
        key="ssh_enabled",
        translation_key="ssh_enabled",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda peer: peer.ssh_enabled,
    ),
    NetBirdPeerBinarySensorEntityDescription(
        key="login_expired",
        translation_key="login_expired",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda peer: peer.login_expired,
    ),
    NetBirdPeerBinarySensorEntityDescription(
        key="approval_required",
        translation_key="approval_required",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda peer: peer.approval_required,
    ),
    NetBirdPeerBinarySensorEntityDescription(
        key="ephemeral",
        translation_key="ephemeral",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda peer: peer.ephemeral,
    ),
)


@dataclass(frozen=True, kw_only=True)
class NetBirdRouteBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a NetBird route binary sensor entity."""

    is_on_fn: Callable[[NetBirdData, NetBirdRoute], bool | None]


ROUTE_BINARY_SENSORS: tuple[NetBirdRouteBinarySensorEntityDescription, ...] = (
    NetBirdRouteBinarySensorEntityDescription(
        key="active",
        translation_key="active",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=lambda data, route: data.is_route_active(route),
    ),
    NetBirdRouteBinarySensorEntityDescription(
        key="enabled",
        translation_key="enabled",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, route: route.enabled,
    ),
)


@dataclass(frozen=True, kw_only=True)
class NetBirdResourceBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a NetBird network resource binary sensor entity."""

    is_on_fn: Callable[[NetBirdData, NetBirdNetworkResource], bool | None]


RESOURCE_BINARY_SENSORS: tuple[NetBirdResourceBinarySensorEntityDescription, ...] = (
    NetBirdResourceBinarySensorEntityDescription(
        key="active",
        translation_key="active",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=lambda data, resource: data.is_resource_active(resource),
    ),
    NetBirdResourceBinarySensorEntityDescription(
        key="enabled",
        translation_key="enabled",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, resource: resource.enabled,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NetBirdConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up NetBird binary sensors based on a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            *(
                NetBirdPeerBinarySensorEntity(
                    coordinator=coordinator, peer=peer, description=description
                )
                for peer in coordinator.data.peers.values()
                for description in PEER_BINARY_SENSORS
            ),
            *(
                NetBirdRouteBinarySensorEntity(
                    coordinator=coordinator, route=route, description=description
                )
                for route in coordinator.data.routes.values()
                for description in ROUTE_BINARY_SENSORS
            ),
            *(
                NetBirdResourceBinarySensorEntity(
                    coordinator=coordinator, resource=resource, description=description
                )
                for resource in coordinator.data.resources.values()
                for description in RESOURCE_BINARY_SENSORS
            ),
        ]
    )


class NetBirdPeerBinarySensorEntity(NetBirdPeerEntity, BinarySensorEntity):
    """Defines a NetBird peer binary sensor."""

    entity_description: NetBirdPeerBinarySensorEntityDescription

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the state of the sensor."""
        peer = self.coordinator.data.peers[self.peer_id]
        return self.entity_description.is_on_fn(peer)


class NetBirdRouteBinarySensorEntity(NetBirdRouteEntity, BinarySensorEntity):
    """Defines a NetBird route binary sensor."""

    entity_description: NetBirdRouteBinarySensorEntityDescription

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the state of the sensor."""
        route = self.coordinator.data.routes[self.route_id]
        return self.entity_description.is_on_fn(self.coordinator.data, route)


class NetBirdResourceBinarySensorEntity(NetBirdResourceEntity, BinarySensorEntity):
    """Defines a NetBird network resource binary sensor."""

    entity_description: NetBirdResourceBinarySensorEntityDescription

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the state of the sensor."""
        resource = self.coordinator.data.resources[self.resource_id]
        return self.entity_description.is_on_fn(self.coordinator.data, resource)
