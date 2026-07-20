"""Support for NetBird sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import NetBirdNetworkResource, NetBirdPeer, NetBirdRoute
from .coordinator import NetBirdConfigEntry
from .entity import NetBirdPeerEntity, NetBirdResourceEntity, NetBirdRouteEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class NetBirdPeerSensorEntityDescription(SensorEntityDescription):
    """Describes a NetBird peer sensor entity."""

    value_fn: Callable[[NetBirdPeer], datetime | str | int | None]


PEER_SENSORS: tuple[NetBirdPeerSensorEntityDescription, ...] = (
    NetBirdPeerSensorEntityDescription(
        key="ip",
        translation_key="ip",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda peer: peer.ip or None,
    ),
    NetBirdPeerSensorEntityDescription(
        key="last_seen",
        translation_key="last_seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda peer: peer.last_seen,
    ),
    NetBirdPeerSensorEntityDescription(
        key="last_login",
        translation_key="last_login",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda peer: peer.last_login,
    ),
    NetBirdPeerSensorEntityDescription(
        key="accessible_peers_count",
        translation_key="accessible_peers_count",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda peer: peer.accessible_peers_count,
    ),
)


@dataclass(frozen=True, kw_only=True)
class NetBirdRouteSensorEntityDescription(SensorEntityDescription):
    """Describes a NetBird route sensor entity."""

    value_fn: Callable[[NetBirdRoute], str | int | None]


ROUTE_SENSORS: tuple[NetBirdRouteSensorEntityDescription, ...] = (
    NetBirdRouteSensorEntityDescription(
        key="destination",
        translation_key="destination",
        value_fn=lambda route: route.destination or None,
    ),
    NetBirdRouteSensorEntityDescription(
        key="route_group",
        translation_key="route_group",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda route: route.network_id or None,
    ),
    NetBirdRouteSensorEntityDescription(
        key="metric",
        translation_key="metric",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda route: route.metric,
    ),
)


@dataclass(frozen=True, kw_only=True)
class NetBirdResourceSensorEntityDescription(SensorEntityDescription):
    """Describes a NetBird network resource sensor entity."""

    value_fn: Callable[[NetBirdNetworkResource], str | None]


RESOURCE_SENSORS: tuple[NetBirdResourceSensorEntityDescription, ...] = (
    NetBirdResourceSensorEntityDescription(
        key="destination",
        translation_key="destination",
        value_fn=lambda resource: resource.address or None,
    ),
    NetBirdResourceSensorEntityDescription(
        key="resource_type",
        translation_key="resource_type",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda resource: resource.type or None,
    ),
    NetBirdResourceSensorEntityDescription(
        key="network_name",
        translation_key="network_name",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda resource: resource.network_name or None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NetBirdConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up NetBird sensors based on a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            *(
                NetBirdPeerSensorEntity(
                    coordinator=coordinator, peer=peer, description=description
                )
                for peer in coordinator.data.peers.values()
                for description in PEER_SENSORS
            ),
            *(
                NetBirdRouteSensorEntity(
                    coordinator=coordinator, route=route, description=description
                )
                for route in coordinator.data.routes.values()
                for description in ROUTE_SENSORS
            ),
            *(
                NetBirdResourceSensorEntity(
                    coordinator=coordinator, resource=resource, description=description
                )
                for resource in coordinator.data.resources.values()
                for description in RESOURCE_SENSORS
            ),
        ]
    )


class NetBirdPeerSensorEntity(NetBirdPeerEntity, SensorEntity):
    """Defines a NetBird peer sensor."""

    entity_description: NetBirdPeerSensorEntityDescription

    @property
    @override
    def native_value(self) -> datetime | str | int | None:
        """Return the state of the sensor."""
        peer = self.coordinator.data.peers[self.peer_id]
        return self.entity_description.value_fn(peer)


class NetBirdRouteSensorEntity(NetBirdRouteEntity, SensorEntity):
    """Defines a NetBird route sensor."""

    entity_description: NetBirdRouteSensorEntityDescription

    @property
    @override
    def native_value(self) -> str | int | None:
        """Return the state of the sensor."""
        route = self.coordinator.data.routes[self.route_id]
        return self.entity_description.value_fn(route)


class NetBirdResourceSensorEntity(NetBirdResourceEntity, SensorEntity):
    """Defines a NetBird network resource sensor."""

    entity_description: NetBirdResourceSensorEntityDescription

    @property
    @override
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        resource = self.coordinator.data.resources[self.resource_id]
        return self.entity_description.value_fn(resource)
