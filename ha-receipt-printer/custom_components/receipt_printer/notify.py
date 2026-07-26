"""Notify platform for the Receipt Printer integration.

Registers `notify.receipt_printer` after the config flow sets up the entry.
Call it with:

Service: notify.receipt_printer
data:
  message: "text to print"
  # or, to print an image by URL:
  data:
    image_url: https://example.com/cat.png
  # or to run a canned task:
  data:
    task_type: fortune
"""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_MESSAGE,
    PLATFORM_SCHEMA,
    NotifyEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, aiohttp_client
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DATA_FAST,
    DATA_IMAGE_URL,
    DATA_TASK_TYPE,
    DEFAULT_PORT,
    DOMAIN,
    ENDPOINT_TEXT,
    ENDPOINT_URL,
    ENDPOINT_TASK,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the notify entity from a config entry."""
    async_add_entities([ReceiptPrinterNotify(hass, entry.data[CONF_HOST], entry.data[CONF_PORT])])


class ReceiptPrinterNotify(NotifyEntity):
    """Entity that proxies messages to the api.py printer service."""

    _attr_name = "Receipt Printer"
    _attr_icon = "mdi:printer-pos"

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        self.hass = hass
        self._host = host
        self._port = port
        self._attr_unique_id = f"{host}:{port}"

    @property
    def base_url(self) -> str:
        return f"http://{self._host}:{self._port}"

    async def async_send_message(self, message: str, **kwargs: Any) -> None:
        """Dispatch the message to the printer.

        Decision order:
          1. data.image_url -> POST /print/url          (message optional)
          2. data.task_type -> POST /print/task          (message is the text)
          3. otherwise      -> POST /print/text          (message is the text)
        """
        data = kwargs.get(ATTR_DATA) or {}
        session = aiohttp_client.async_get_clientsession(self.hass)

        try:
            if image_url := data.get(DATA_IMAGE_URL):
                await self._post_multipart(
                    session,
                    ENDPOINT_URL,
                    fields={"url": image_url},
                )
            elif task_type := data.get(DATA_TASK_TYPE):
                await self._post_multipart(
                    session,
                    ENDPOINT_TASK,
                    fields={"text": message, "task_type": task_type},
                )
            else:
                fast = "1" if data.get(DATA_FAST) else "0"
                await self._post_multipart(
                    session,
                    ENDPOINT_TEXT,
                    fields={"text": message, "fast": fast},
                )
        except aiohttp.ClientError as err:
            _LOGGER.error("Receipt printer request failed: %s", err)
            raise

    async def _post_multipart(
        self,
        session: aiohttp.ClientSession,
        path: str,
        fields: dict[str, str],
    ) -> dict[str, Any]:
        """POST a multipart/form-data request and return parsed JSON."""
        form = aiohttp.FormData()
        for k, v in fields.items():
            form.add_field(k, v)
        async with session.post(
            f"{self.base_url}{path}",
            data=form,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            resp.raise_for_status()
            # api.py returns JSON on success/error
            if resp.headers.get("content-type", "").startswith("application/json"):
                return await resp.json()
            return {}