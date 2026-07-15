"""Utilities for Ultraloq BLE integration."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import LOGGER, UL_ERRORS
from .enrollment import normalize_api_devices
from .utecio.api import InvalidCredentials, InvalidResponse, UtecClient


async def async_enroll_api_devices(
    hass: HomeAssistant, email: str, password: str
) -> list[dict[str, str]]:
    """Fetch and minimize the device metadata needed for local BLE use."""

    devices = normalize_api_devices(
        await async_fetch_api_devices(hass, email, password)
    )
    if not devices:
        LOGGER.error("Could not retrieve any locks from Utec servers")
        raise NoDevicesError
    return devices


async def async_fetch_api_devices(
    hass: HomeAssistant, email: str, password: str
) -> list[dict[str, Any]]:
    """Fetch raw device metadata from the UTEC cloud API."""

    client = UtecClient(
        email=email, password=password, session=async_get_clientsession(hass)
    )

    try:
        return await client.get_json()
    except UL_ERRORS as err:
        LOGGER.error("Failed to get information from UTEC servers")
        raise ConnectionError from err
    except InvalidCredentials:
        LOGGER.error("Failed to login to UTEC servers")
        raise
    except InvalidResponse as err:
        LOGGER.error("Received an unexpected response from UTEC servers")
        raise ConnectionError from err


class NoDevicesError(Exception):
    """No Locks from UTECIO API."""
