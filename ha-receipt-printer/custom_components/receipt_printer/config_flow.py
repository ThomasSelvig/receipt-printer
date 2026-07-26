"""Config flow for Receipt Printer.

Lets the user enter the host/port of the api.py service in the HA UI so the
integration can be added under Settings -> Devices & Services instead of YAML.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import aiohttp_client
import aiohttp

from .const import DEFAULT_PORT, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
    }
)


async def _can_reach_print_text(hass: HomeAssistant, host: str, port: int) -> bool:
    """Lightweight connectivity check: a wrong method still returns a JSON
    response from FastAPI, which tells us the server is alive."""
    url = f"http://{host}:{port}/print/text"
    try:
        session = aiohttp_client.async_get_clientsession(hass)
        # GET /print/text is not defined -> FastAPI returns 405. The fact we
        # got an HTTP response (not a connection error) is enough validation.
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            return resp.status == 405 or resp.status == 404 or resp.ok
    except (aiohttp.ClientError, TimeoutError):
        return False


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Receipt Printer."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            if await _can_reach_print_text(self.hass, host, port):
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Receipt Printer @ {host}:{port}",
                    data={CONF_HOST: host, CONF_PORT: port},
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )