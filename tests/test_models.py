"""Tests for lock model mapping."""

from custom_components.ultraloq_ble.utecio import DeviceLockUBolt, known_devices
from custom_components.ultraloq_ble.utecio.ble.lock import UtecBleLock


def test_original_u_bolt_model_is_ble_capable(enrolled_u_bolt):
    """The original U-Bolt retains its direct BLE capability mapping."""

    assert isinstance(known_devices["U-Bolt"], DeviceLockUBolt)
    lock = UtecBleLock.from_enrollment(enrolled_u_bolt)

    assert lock.model == "U-Bolt"
    assert lock.capabilities.bluetooth is True
    assert lock.capabilities.autolock is True
    assert lock.capabilities.bt264 is True
