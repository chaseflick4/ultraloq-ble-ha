"""Tests for diagnostics redaction and allowlisting."""

import json
from types import SimpleNamespace

from custom_components.ultraloq_ble.const import DOMAIN, UTEC_LOCKDATA
from custom_components.ultraloq_ble.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics_never_export_identifiers_or_secrets():
    """All sensitive entry/device fields remain outside diagnostics output."""

    sentinels = {
        "email": "owner-secret@example.com",
        "password": "XTHINGS-PASSWORD-SENTINEL",
        "uid": "UID-SENTINEL",
        "admin_pin": "PIN-SENTINEL",
        "token": "TOKEN-SENTINEL",
        "address": "AA:BB:CC:DD:EE:FF",
        "serialnumber": "SERIAL-SENTINEL",
        "packet": "PACKET-SENTINEL",
        "key": "KEY-SENTINEL",
    }
    entry = SimpleNamespace(
        entry_id="entry-id",
        version=2,
        minor_version=1,
        data=sentinels,
    )
    device = SimpleNamespace(
        model="U-Bolt",
        _ha_available=True,
        lock_status=2,
        battery=3,
        **sentinels,
    )
    hass = SimpleNamespace(
        data={DOMAIN: {entry.entry_id: {UTEC_LOCKDATA: [device]}}}
    )

    result = await async_get_config_entry_diagnostics(hass, entry)
    serialized = json.dumps(result, sort_keys=True)

    for sentinel in sentinels.values():
        assert sentinel not in serialized
    assert result["entry"]["models"] == {"U-Bolt": 1}
    assert result["transport"]["available_device_count"] == 1
