"""Tests for Home Assistant-selected local and proxy BLE transports."""

from unittest.mock import MagicMock, patch

import pytest

from custom_components.ultraloq_ble.lock import UtecLock
from custom_components.ultraloq_ble.utecio.ble.lock import UtecBleLock


@pytest.mark.asyncio
async def test_connectable_device_from_ha_is_used_for_gatt(enrolled_u_bolt):
    """HA may return either a local adapter or active ESPHome proxy device."""

    lock = UtecBleLock.from_enrollment(enrolled_u_bolt)
    entity = UtecLock(MagicMock(), lock, scan_interval=300, poll_offset=0)
    entity.hass = MagicMock()
    selected_by_ha = object()

    with patch(
        "custom_components.ultraloq_ble.lock.bluetooth.async_ble_device_from_address",
        return_value=selected_by_ha,
    ) as lookup:
        result = await entity.async_bledevice_callback(lock.mac_uuid)

    assert result is selected_by_ha
    lookup.assert_called_once_with(entity.hass, lock.mac_uuid, connectable=True)
