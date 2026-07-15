"""Ultraloq BLE component."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import (
    CONF_API_DEVICES,
    CONF_ENROLLED_DEVICES,
    DOMAIN,
    LOGGER,
    PLATFORMS,
    UPDATE_LISTENER,
    UTEC_LOCKDATA,
)
from .enrollment import account_unique_id, normalize_api_devices
from .utecio import known_devices
from .utecio.ble.lock import UtecBleLock
from .util import async_enroll_api_devices


def debug_mode():
    """Is integration in debug mode."""
    return LOGGER.isEnabledFor(logging.DEBUG)


def _build_ble_devices(
    enrolled_devices: list[dict[str, Any]],
) -> list[UtecBleLock]:
    """Build BLE lock objects from minimized cached enrollment metadata."""

    devices: list[UtecBleLock] = []
    for enrolled_device in enrolled_devices:
        device = UtecBleLock.from_enrollment(enrolled_device)
        capabilities = device.capabilities
        if isinstance(capabilities, type):
            try:
                capabilities = capabilities()
            except Exception as err:
                LOGGER.warning(
                    "Failed to initialize capabilities for model %s: %s",
                    device.model,
                    err,
                )
                capabilities = None
            else:
                device.capabilities = capabilities

        if getattr(capabilities, "bluetooth", False):
            devices.append(device)
            if device.model not in known_devices:
                LOGGER.warning(
                    "Treating unknown Ultraloq model as BLE-capable: %s", device.model
                )
        else:
            LOGGER.debug("Skipping non-BLE or unknown Ultraloq model %s", device.model)

    return devices


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Replace stored cloud credentials and raw API data with a minimal cache."""

    if entry.version >= 2:
        return True

    email = entry.data.get(CONF_EMAIL)
    try:
        if raw_devices := entry.data.get(CONF_API_DEVICES):
            enrolled_devices = normalize_api_devices(raw_devices)
        elif email and (password := entry.data.get(CONF_PASSWORD)):
            enrolled_devices = await async_enroll_api_devices(hass, email, password)
        else:
            LOGGER.error("Cannot migrate Ultraloq entry without enrollment metadata")
            return False
    except Exception as err:
        LOGGER.error(
            "Could not migrate Ultraloq enrollment (%s)", type(err).__name__
        )
        return False

    if not enrolled_devices:
        LOGGER.error("Cannot migrate Ultraloq entry with no BLE devices")
        return False

    unique_id = account_unique_id(email) if email else entry.unique_id
    hass.config_entries.async_update_entry(
        entry,
        data={CONF_ENROLLED_DEVICES: enrolled_devices},
        unique_id=unique_id,
        version=2,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Lock from a config entry."""

    enrolled_devices = entry.data.get(CONF_ENROLLED_DEVICES)
    if not enrolled_devices:
        raise ConfigEntryNotReady(
            "Ultraloq BLE enrollment is missing; run reconfigure to refresh it"
        )

    devices = _build_ble_devices(enrolled_devices)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {UTEC_LOCKDATA: devices}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    update_listener = entry.add_update_listener(async_update_options)
    hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER] = update_listener

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Ultraloq config entry."""

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        update_listener = hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER]
        update_listener()
        del hass.data[DOMAIN][entry.entry_id]
        if not hass.data[DOMAIN]:
            del hass.data[DOMAIN]
    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""

    await hass.config_entries.async_reload(entry.entry_id)
