"""The Receipt Printer integration.”

Forwards setup to the notify platform. A config entry holds the host/port of
the api.py service running on the desktop PC.
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: tuple[Platform, ...] = (Platform.NOTIFY,)

SERVICE_PRINT_IMAGE = "print_image"
ATTR_FILE_PATH = "file_path"


async def _print_image_service(hass: HomeAssistant, entry_data, call) -> None:
    """Handle `receipt_printer.print_image` service calls.

    Reads a file from the HA server filesystem and POSTs it as multipart/form-data
    to /print/image on the configured api.py service. Useful for automations
    (e.g. print a camera snapshot after motion).
    """
    import os
    import aiohttp
    from homeassistant.helpers import aiohttp_client

    file_path = call.data[ATTR_FILE_PATH]
    if not os.path.isfile(file_path):
        _LOGGER.error("print_image: file not found: %s", file_path)
        return

    host = entry_data[CONF_HOST]
    port = entry_data[CONF_PORT]
    url = f"http://{host}:{port}/print/image"

    def _read() -> bytes:
        with open(file_path, "rb") as f:
            return f.read()

    data_bytes = await hass.async_add_executor_job(_read)
    session = aiohttp_client.async_get_clientsession(hass)
    form = aiohttp.FormData()
    form.add_field(
        "file",
        data_bytes,
        filename=os.path.basename(file_path),
        content_type="image/png",
    )
    try:
        async with session.post(url, data=form, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            resp.raise_for_status()
            if resp.headers.get("content-type", "").startswith("application/json"):
                _LOGGER.info("print_image response: %s", await resp.json())
    except aiohttp.ClientError as err:
        _LOGGER.error("print_image: upload failed: %s", err)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Receipt Printer from a config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data

    # Register the print_image service. It needs the entry's host/port, so we
    # bind it via a closure on entry.entry_id and look up data at call time.
    async def _handle_print_image(call):
        entry_data = hass.data[DOMAIN][entry.entry_id]
        await _print_image_service(hass, entry_data, call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_PRINT_IMAGE,
        _handle_print_image,
        schema=vol.Schema({vol.Required(ATTR_FILE_PATH): str}),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.services.async_remove(DOMAIN, SERVICE_PRINT_IMAGE)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok