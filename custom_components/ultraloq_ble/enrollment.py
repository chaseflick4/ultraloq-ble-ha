"""Normalize cloud-assisted enrollment data for local BLE use."""
from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from typing import Any

from .const import (
    ENROLLMENT_ADDRESS,
    ENROLLMENT_ADMIN_PIN,
    ENROLLMENT_MODEL,
    ENROLLMENT_NAME,
    ENROLLMENT_UID,
    ENROLLMENT_WAKE_ADDRESS,
)
from .utecio.util import decode_password


class InvalidEnrollmentData(ValueError):
    """Raised when cloud enrollment data cannot support local BLE control."""


def account_unique_id(email: str) -> str:
    """Return a stable, non-reversible identifier for an Xthings account."""

    normalized = email.strip().casefold().encode()
    return hashlib.sha256(normalized).hexdigest()


def normalize_api_device(api_device: Mapping[str, Any]) -> dict[str, str]:
    """Keep only the lock metadata required for local BLE operation."""

    try:
        user = api_device["user"]
        params = api_device.get("params", {})
        if not isinstance(user, Mapping) or not isinstance(params, Mapping):
            raise TypeError

        name = str(api_device["name"])
        model = str(api_device["model"])
        address = str(api_device["uuid"])
        uid = str(user["uid"])
        admin_pin = decode_password(int(user["password"]))
        wake_address = str(params.get("extend_ble") or "")
    except (KeyError, TypeError, ValueError) as err:
        raise InvalidEnrollmentData(
            "The Xthings response did not contain required BLE enrollment fields."
        ) from err

    if not all((name, model, address, uid, admin_pin)):
        raise InvalidEnrollmentData(
            "The Xthings response contained empty BLE enrollment fields."
        )

    return {
        ENROLLMENT_NAME: name,
        ENROLLMENT_MODEL: model,
        ENROLLMENT_ADDRESS: address,
        ENROLLMENT_WAKE_ADDRESS: wake_address,
        ENROLLMENT_UID: uid,
        ENROLLMENT_ADMIN_PIN: admin_pin,
    }


def normalize_api_devices(
    api_devices: Iterable[Mapping[str, Any]],
) -> list[dict[str, str]]:
    """Normalize and de-duplicate cloud device records."""

    normalized: list[dict[str, str]] = []
    seen_addresses: set[str] = set()
    for api_device in api_devices:
        device = normalize_api_device(api_device)
        address = device[ENROLLMENT_ADDRESS]
        if address in seen_addresses:
            continue
        seen_addresses.add(address)
        normalized.append(device)
    return normalized
