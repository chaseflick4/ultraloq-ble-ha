"""Shared fixtures for Ultraloq BLE tests."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow loading this custom integration in Home Assistant tests."""

    yield


@pytest.fixture
def raw_u_bolt_device():
    """Return synthetic cloud enrollment data with no real lock secrets."""

    return {
        "name": "Fixture Lock",
        "model": "U-Bolt",
        "uuid": "AA:BB:CC:DD:EE:FF",
        "user": {"uid": 123456, "password": 0x400004D2},
        "params": {
            "extend_ble": "11:22:33:44:55:66",
            "serialnumber": "SERIAL-MUST-NOT-PERSIST",
        },
        "token": "TOKEN-MUST-NOT-PERSIST",
        "unknown_remote_field": "REMOTE-MUST-NOT-PERSIST",
    }


@pytest.fixture
def enrolled_u_bolt():
    """Return synthetic, minimized local BLE enrollment data."""

    return {
        "name": "Fixture Lock",
        "model": "U-Bolt",
        "address": "AA:BB:CC:DD:EE:FF",
        "wake_address": "11:22:33:44:55:66",
        "uid": "123456",
        "admin_pin": "1234",
    }
