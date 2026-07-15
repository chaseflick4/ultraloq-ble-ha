"""Tests for minimized cloud-assisted enrollment."""

from custom_components.ultraloq_ble.enrollment import (
    account_unique_id,
    normalize_api_device,
)


def test_normalize_api_device_keeps_only_ble_fields(raw_u_bolt_device):
    """Raw cloud payloads are reduced to the strict local BLE allowlist."""

    result = normalize_api_device(raw_u_bolt_device)

    assert result == {
        "name": "Fixture Lock",
        "model": "U-Bolt",
        "address": "AA:BB:CC:DD:EE:FF",
        "wake_address": "11:22:33:44:55:66",
        "uid": "123456",
        "admin_pin": "1234",
    }
    serialized = repr(result)
    assert "SERIAL-MUST-NOT-PERSIST" not in serialized
    assert "TOKEN-MUST-NOT-PERSIST" not in serialized
    assert "REMOTE-MUST-NOT-PERSIST" not in serialized


def test_account_unique_id_is_stable_and_non_reversible():
    """The account email is represented only by a stable hash."""

    email = "Owner.Example@example.com"
    result = account_unique_id(email)

    assert result == account_unique_id(" owner.example@EXAMPLE.com ")
    assert len(result) == 64
    assert email not in result
