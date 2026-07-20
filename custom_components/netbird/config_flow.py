"""Config flow to configure the NetBird integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, override

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    NetBirdAccount,
    NetBirdApiClient,
    NetBirdAuthenticationError,
    NetBirdError,
)
from .const import DEFAULT_API_URL, DOMAIN

TOKENS_URL = "https://app.netbird.io/team"


async def validate_input(
    hass: HomeAssistant, *, api_url: str, api_key: str
) -> NetBirdAccount:
    """Try using the given API URL & key against the NetBird API."""
    session = async_get_clientsession(hass)
    client = NetBirdApiClient(session=session, api_url=api_url, api_key=api_key)
    return await client.get_account()


class NetBirdFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for NetBird."""

    VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            try:
                account = await validate_input(
                    self.hass,
                    api_url=user_input[CONF_URL],
                    api_key=user_input[CONF_API_KEY],
                )
            except NetBirdAuthenticationError:
                errors["base"] = "invalid_auth"
            except NetBirdError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(account.id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=account.domain or "NetBird",
                    data={
                        CONF_URL: user_input[CONF_URL],
                        CONF_API_KEY: user_input[CONF_API_KEY],
                    },
                )
        else:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            description_placeholders={"tokens_url": TOKENS_URL},
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_URL, default=user_input.get(CONF_URL, DEFAULT_API_URL)
                    ): str,
                    vol.Required(
                        CONF_API_KEY, default=user_input.get(CONF_API_KEY, "")
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle initiation of re-authentication with NetBird."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-authentication with NetBird."""
        errors = {}

        if user_input is not None:
            reauth_entry = self._get_reauth_entry()
            try:
                await validate_input(
                    self.hass,
                    api_url=reauth_entry.data[CONF_URL],
                    api_key=user_input[CONF_API_KEY],
                )
            except NetBirdAuthenticationError:
                errors["base"] = "invalid_auth"
            except NetBirdError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={CONF_API_KEY: user_input[CONF_API_KEY]},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            description_placeholders={"tokens_url": TOKENS_URL},
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )
