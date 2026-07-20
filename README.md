# NetBird for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A custom Home Assistant integration that monitors your [NetBird](https://netbird.io) network: peers, legacy routes and network resources (with their routers).

This integration **only monitors** your NetBird network. It does **not** make your Home Assistant instance accessible via the NetBird VPN.

## Features

- One device per peer, route and network resource, with sensors and binary sensors for their state (connected/active, IP, last seen, last login, SSH enabled, login expired, approval required, accessible peers, and more).
- Works against NetBird's cloud API or a self-hosted management server.
- Re-authentication flow if your API token is revoked or expires.
- Stale devices (removed peers/routes/resources) are cleaned up automatically.
- An example fully dynamic [Lovelace dashboard](dashboard.yaml) that lists all peers/routes/resources without needing to hardcode entity IDs.

## Installation

### Via HACS (recommended)

1. In Home Assistant, go to **HACS**.
2. Open the three-dot menu (top right) -> **Custom repositories**.
3. Add this repository URL (`https://github.com/jose1711/netbird-ha`), category **Integration**.
4. Find "NetBird" in HACS and install it.
5. Restart Home Assistant.

### Manual

1. Copy the `custom_components/netbird` folder into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. In Home Assistant, go to **Settings -> Devices & services -> Add integration**, search for "NetBird".
2. Create a Personal Access Token in the [NetBird dashboard](https://app.netbird.io/team) and paste it in.
3. Leave the API URL as-is for NetBird's cloud service, or point it at your self-hosted management server's API URL (e.g. `https://api.netbird.example.com`).

## Dashboard

An example dashboard is provided in [`dashboard.yaml`](dashboard.yaml). It auto-discovers all NetBird devices via Home Assistant's built-in templating, so it keeps working as peers are added or removed, no manual entity list to maintain. See the comments at the top of that file for how to add it.

## Known NetBird API limitations

- The "Accessible peers" count is not provided by NetBird's bulk peers listing endpoint (it always reports 0 there); this integration fetches the real count per peer once at startup instead of on every poll, to avoid excessive API calls.

## License

[MIT](LICENSE)
