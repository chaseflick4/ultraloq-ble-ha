"""Non-physical tests for Home Assistant lock state transitions."""

from unittest.mock import MagicMock

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.ultraloq_ble.lock import UtecLock
from custom_components.ultraloq_ble.utecio.ble.device import UtecBleDeviceError
from custom_components.ultraloq_ble.utecio.ble.lock import UtecBleLock
from custom_components.ultraloq_ble.utecio.enums import DeviceLockStatus


def _entity(enrolled_u_bolt):
    lock = UtecBleLock.from_enrollment(enrolled_u_bolt)
    return UtecLock(MagicMock(), lock, scan_interval=300, poll_offset=0)


def test_sync_state_clears_transitions(enrolled_u_bolt):
    """Confirmed protocol states clear optimistic transition flags."""

    entity = _entity(enrolled_u_bolt)
    entity._attr_is_locking = True
    entity.lock.lock_status = DeviceLockStatus.LOCKED.value
    entity._sync_state_from_lock()
    assert entity.is_locked is True
    assert entity.is_locking is False

    entity._attr_is_unlocking = True
    entity.lock.lock_status = DeviceLockStatus.UNLOCKED.value
    entity._sync_state_from_lock()
    assert entity.is_locked is False
    assert entity.is_unlocking is False


def test_autolock_due_requests_status_instead_of_inventing_state(
    enrolled_u_bolt,
):
    """An elapsed timer polls the lock and never asserts physical locking."""

    entity = _entity(enrolled_u_bolt)
    entity._attr_is_locked = False
    entity.request_update = MagicMock()

    entity._handle_autolock_due(None)

    assert entity.is_locked is False
    entity.request_update.assert_called_once_with()


@pytest.mark.asyncio
async def test_unlock_failure_propagates_to_home_assistant(enrolled_u_bolt):
    """A failed BLE write is visible to the service caller."""

    entity = _entity(enrolled_u_bolt)
    entity.lock.async_unlock = MagicMock(
        side_effect=UtecBleDeviceError("synthetic failure")
    )
    entity._schedule_transition_timeout = MagicMock()
    entity.async_write_ha_state = MagicMock()

    with pytest.raises(HomeAssistantError):
        await entity.async_unlock()
