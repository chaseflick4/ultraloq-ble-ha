"""Privacy-preserving diagnostics for Ultraloq BLE."""
from __future__ import annotations

from collections import Counter
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, UTEC_LOCKDATA

SENSITIVE_KEYS = {
    "address",
    "admin_pin",
    "api_devices",
    "ble_address",
    "ciphertext",
    "email",
    "encrypted_packet",
    "key",
    "mac",
    "mac_uuid",
    "mobile_uuid",
    "packet",
    "password",
    "pin",
    "plaintext",
    "serial",
    "serial_number",
    "serialnumber",
    "sn",
    "token",
    "uid",
    "uuid",
    "wake_address",
    "wurx_uuid",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return allowlist-only diagnostics without lock or account identifiers."""

    devices = (
        hass.data.get(DOMAIN, {})
        .get(entry.entry_id, {})
        .get(UTEC_LOCKDATA, [])
    )
    models = Counter(device.model or "unknown" for device in devices)

    diagnostics = {
        "entry": {
            "version": entry.version,
            "minor_version": entry.minor_version,
            "device_count": len(devices),
            "models": dict(sorted(models.items())),
            "legacy_cloud_credentials_present": any(
                key in entry.data for key in ("email", "password")
            ),
        },
        "transport": {
            "local_ble": True,
            "active_connection_required": True,
            "available_device_count": sum(
                bool(getattr(device, "_ha_available", False)) for device in devices
            ),
        },
        "devices": [
            {
                "model": device.model or "unknown",
                "available": bool(getattr(device, "_ha_available", False)),
                "lock_state_known": getattr(device, "lock_status", -1) >= 0,
                "battery_state_known": getattr(device, "battery", -1) >= 0,
            }
            for device in devices
        ],
    }
    return async_redact_data(diagnostics, SENSITIVE_KEYS)
