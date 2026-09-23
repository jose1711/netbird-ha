"""Thin async client for the NetBird management API.

Reference: https://docs.netbird.io/api
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

REQUEST_TIMEOUT = ClientTimeout(total=15)


def _parse_timestamp(value: str | None) -> datetime | None:
    """Parse an RFC3339 timestamp from the NetBird API into a datetime.

    Returns None for missing values and for Go's zero-time sentinel
    ("0001-01-01T00:00:00Z"), which the API uses when a peer has never
    connected or logged in.
    """
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.year < 1971:
        return None
    return parsed


class NetBirdError(Exception):
    """Generic NetBird API error."""


class NetBirdConnectionError(NetBirdError):
    """Raised when the NetBird API cannot be reached."""


class NetBirdAuthenticationError(NetBirdError):
    """Raised when the NetBird API token is invalid or lacks permission."""


@dataclass
class NetBirdGroup:
    """A group a peer or resource belongs to."""

    id: str
    name: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetBirdGroup:
        """Build a group from the API response."""
        return cls(id=data["id"], name=data.get("name", ""))


@dataclass
class NetBirdPeer:
    """Representation of a single NetBird peer."""

    id: str
    name: str
    hostname: str
    ip: str
    os: str
    version: str
    connected: bool
    last_seen: datetime | None
    last_login: datetime | None
    ssh_enabled: bool
    login_expired: bool
    login_expiration_enabled: bool
    approval_required: bool
    ephemeral: bool
    accessible_peers_count: int
    groups: list[NetBirdGroup] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    login_expires_at: datetime | None = field(default=None, init=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetBirdPeer:
        """Build a peer from the API response."""
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            hostname=data.get("hostname", ""),
            ip=data.get("ip", ""),
            os=data.get("os", ""),
            version=data.get("version", ""),
            connected=data.get("connected", False),
            last_seen=_parse_timestamp(data.get("last_seen")),
            last_login=_parse_timestamp(data.get("last_login")),
            ssh_enabled=data.get("ssh_enabled", False),
            login_expired=data.get("login_expired", False),
            login_expiration_enabled=data.get("login_expiration_enabled", False),
            approval_required=data.get("approval_required", False),
            ephemeral=data.get("ephemeral", False),
            accessible_peers_count=data.get("accessible_peers_count", 0),
            groups=[NetBirdGroup.from_dict(g) for g in data.get("groups") or []],
            raw=data,
        )

    @property
    def group_ids(self) -> set[str]:
        """Return the IDs of the groups this peer belongs to."""
        return {group.id for group in self.groups}


@dataclass
class NetBirdRoute:
    """A legacy NetBird network route (destination network/domain)."""

    id: str
    network_id: str
    description: str
    enabled: bool
    metric: int
    network: str | None
    domains: list[str] = field(default_factory=list)
    peer: str | None = None
    peer_groups: list[str] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)

    @property
    def destination(self) -> str:
        """Return a human-readable destination for this route."""
        if self.network:
            return self.network
        if self.domains:
            return ", ".join(self.domains)
        return ""

    @property
    def serving_peer_group_ids(self) -> set[str]:
        """Return group IDs of peers that may serve this route."""
        return set(self.peer_groups) | set(self.groups)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetBirdRoute:
        """Build a route from the API response."""
        return cls(
            id=data["id"],
            network_id=data.get("network_id", ""),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            metric=data.get("metric", 9999),
            network=data.get("network"),
            domains=data.get("domains") or [],
            peer=data.get("peer"),
            peer_groups=data.get("peer_groups") or [],
            groups=data.get("groups") or [],
        )


@dataclass
class NetBirdNetwork:
    """A NetBird network (the newer Networks/Resources routing model)."""

    id: str
    name: str
    description: str
    routing_peers_count: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetBirdNetwork:
        """Build a network from the API response."""
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            routing_peers_count=data.get("routing_peers_count", 0),
        )


@dataclass
class NetBirdNetworkResource:
    """A destination (host/subnet/domain) inside a NetBird network."""

    id: str
    network_id: str
    network_name: str
    name: str
    address: str
    type: str
    description: str
    enabled: bool
    groups: list[NetBirdGroup] = field(default_factory=list)

    @classmethod
    def from_dict(
        cls, network_id: str, network_name: str, data: dict[str, Any]
    ) -> NetBirdNetworkResource:
        """Build a network resource from the API response."""
        return cls(
            id=data["id"],
            network_id=network_id,
            network_name=network_name,
            name=data.get("name", ""),
            address=data.get("address", ""),
            type=data.get("type", "host"),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            groups=[NetBirdGroup.from_dict(g) for g in data.get("groups") or []],
        )


@dataclass
class NetBirdNetworkRouter:
    """A peer (or peer group) that routes traffic for a NetBird network."""

    id: str
    enabled: bool
    metric: int
    peer: str | None
    peer_groups: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetBirdNetworkRouter:
        """Build a network router from the API response."""
        return cls(
            id=data["id"],
            enabled=data.get("enabled", True),
            metric=data.get("metric", 9999),
            peer=data.get("peer"),
            peer_groups=data.get("peer_groups") or [],
        )


@dataclass
class NetBirdAccount:
    """A NetBird account tied to the API token used to authenticate."""

    id: str
    domain: str
    peer_login_expiration_enabled: bool
    peer_login_expiration: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetBirdAccount:
        """Build an account from the API response."""
        settings = data.get("settings") or {}
        return cls(
            id=data["id"],
            domain=data.get("domain", ""),
            peer_login_expiration_enabled=settings.get(
                "peer_login_expiration_enabled", False
            ),
            peer_login_expiration=settings.get("peer_login_expiration", 0),
        )


@dataclass
class NetBirdData:
    """A snapshot of everything the coordinator fetched from NetBird."""

    peers: dict[str, NetBirdPeer] = field(default_factory=dict)
    routes: dict[str, NetBirdRoute] = field(default_factory=dict)
    resources: dict[str, NetBirdNetworkResource] = field(default_factory=dict)
    routers: dict[str, list[NetBirdNetworkRouter]] = field(default_factory=dict)

    def _peers_in_groups(self, group_ids: set[str]) -> set[str]:
        """Return IDs of peers that belong to any of the given groups."""
        if not group_ids:
            return set()
        return {
            peer.id for peer in self.peers.values() if peer.group_ids & group_ids
        }

    def route_serving_peer_ids(self, route: NetBirdRoute) -> set[str]:
        """Return IDs of peers that can serve the given route."""
        peer_ids = {route.peer} if route.peer else set()
        peer_ids |= self._peers_in_groups(route.serving_peer_group_ids)
        return {peer_id for peer_id in peer_ids if peer_id}

    def is_route_active(self, route: NetBirdRoute) -> bool:
        """Return True if the route is enabled and served by a connected peer."""
        if not route.enabled:
            return False
        serving_peer_ids = self.route_serving_peer_ids(route)
        return any(
            self.peers[peer_id].connected
            for peer_id in serving_peer_ids
            if peer_id in self.peers
        )

    def network_serving_peer_ids(self, network_id: str) -> set[str]:
        """Return IDs of peers that route traffic for the given network."""
        peer_ids: set[str] = set()
        for router in self.routers.get(network_id, []):
            if not router.enabled:
                continue
            if router.peer:
                peer_ids.add(router.peer)
            peer_ids |= self._peers_in_groups(set(router.peer_groups))
        return peer_ids

    def is_resource_active(self, resource: NetBirdNetworkResource) -> bool:
        """Return True if the resource is enabled and reachable via a connected router."""
        if not resource.enabled:
            return False
        serving_peer_ids = self.network_serving_peer_ids(resource.network_id)
        return any(
            self.peers[peer_id].connected
            for peer_id in serving_peer_ids
            if peer_id in self.peers
        )


class NetBirdApiClient:
    """Minimal async wrapper around the NetBird management API."""

    def __init__(self, session: ClientSession, api_url: str, api_key: str) -> None:
        """Initialize the client."""
        self._session = session
        self._api_url = api_url.rstrip("/")
        self._headers = {
            "Authorization": f"Token {api_key}",
            "Accept": "application/json",
        }

    async def _get(self, path: str) -> Any:
        """Perform a GET request against the NetBird API."""
        try:
            async with self._session.get(
                f"{self._api_url}{path}",
                headers=self._headers,
                timeout=REQUEST_TIMEOUT,
            ) as response:
                if response.status in (401, 403):
                    raise NetBirdAuthenticationError(
                        "Invalid or unauthorized NetBird API token"
                    )
                if response.status >= 400:
                    body = await response.text()
                    raise NetBirdConnectionError(
                        f"Unexpected response from NetBird API "
                        f"({response.status}): {body}"
                    )
                return await response.json()
        except ClientError as err:
            raise NetBirdConnectionError(
                f"Error communicating with NetBird API: {err}"
            ) from err

    async def get_peers(self) -> dict[str, NetBirdPeer]:
        """Return all peers, keyed by peer ID."""
        data = await self._get("/api/peers")
        return {peer["id"]: NetBirdPeer.from_dict(peer) for peer in data}

    async def get_routes(self) -> dict[str, NetBirdRoute]:
        """Return all legacy network routes, keyed by route ID."""
        data = await self._get("/api/routes")
        return {route["id"]: NetBirdRoute.from_dict(route) for route in data}

    async def get_networks(self) -> list[NetBirdNetwork]:
        """Return all networks."""
        data = await self._get("/api/networks")
        return [NetBirdNetwork.from_dict(network) for network in data]

    async def get_network_resources(
        self, network_id: str, network_name: str
    ) -> list[NetBirdNetworkResource]:
        """Return all resources (destinations) in a network."""
        data = await self._get(f"/api/networks/{network_id}/resources")
        return [
            NetBirdNetworkResource.from_dict(network_id, network_name, resource)
            for resource in data
        ]

    async def get_network_routers(self, network_id: str) -> list[NetBirdNetworkRouter]:
        """Return all routers (routing peers) of a network."""
        data = await self._get(f"/api/networks/{network_id}/routers")
        return [NetBirdNetworkRouter.from_dict(router) for router in data]

    async def get_routing_data(
        self,
    ) -> tuple[dict[str, NetBirdNetworkResource], dict[str, list[NetBirdNetworkRouter]]]:
        """Fetch every network's resources and routers.

        Returns resources keyed by resource ID, and routers grouped by network ID.
        """
        networks = await self.get_networks()
        if not networks:
            return {}, {}

        results = await asyncio.gather(
            *(self.get_network_resources(n.id, n.name) for n in networks),
            *(self.get_network_routers(n.id) for n in networks),
        )
        resource_lists = results[: len(networks)]
        router_lists = results[len(networks) :]

        resources: dict[str, NetBirdNetworkResource] = {}
        routers: dict[str, list[NetBirdNetworkRouter]] = {}
        for network, network_resources, network_routers in zip(
            networks, resource_lists, router_lists, strict=True
        ):
            for resource in network_resources:
                resources[resource.id] = resource
            routers[network.id] = network_routers

        return resources, routers

    async def get_accessible_peers_count(self, peer_id: str) -> int:
        """Return how many peers the given peer can currently connect to.

        The bulk /api/peers listing always reports 0 for this value (a
        NetBird API limitation), so it has to be fetched per peer instead.
        """
        data = await self._get(f"/api/peers/{peer_id}/accessible-peers")
        return len(data)

    async def get_accessible_peers_counts(
        self, peer_ids: list[str]
    ) -> dict[str, int]:
        """Return accessible peer counts for multiple peers, keyed by peer ID."""
        counts = await asyncio.gather(
            *(self.get_accessible_peers_count(peer_id) for peer_id in peer_ids)
        )
        return dict(zip(peer_ids, counts, strict=True))

    async def get_account(self) -> NetBirdAccount:
        """Return the NetBird account tied to the API token."""
        accounts = await self._get("/api/accounts")
        if not accounts:
            raise NetBirdError("No NetBird account found for this API token")
        return NetBirdAccount.from_dict(accounts[0])
