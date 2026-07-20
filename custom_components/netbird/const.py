"""Constants for the NetBird integration."""

from datetime import timedelta
import logging
from typing import Final

DOMAIN: Final = "netbird"

LOGGER = logging.getLogger(__package__)
SCAN_INTERVAL = timedelta(minutes=1)

DEFAULT_API_URL: Final = "https://api.netbird.io"
