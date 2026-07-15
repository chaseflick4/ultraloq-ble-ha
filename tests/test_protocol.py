"""Golden-vector and secret-safe logging tests for the BLE protocol."""

import logging
from types import SimpleNamespace

import pytest

from custom_components.ultraloq_ble.utecio.api import InvalidResponse, UtecClient
from custom_components.ultraloq_ble.utecio.ble.device import (
    UtecBleDevice,
    UtecBleDeviceKey,
    UtecBleRequest,
    UtecBleResponse,
)
from custom_components.ultraloq_ble.utecio.enums import BLECommandCode


def test_authenticated_packet_and_encryption_golden_vectors():
    """Synthetic auth framing, CRC, and AES-CBC output remain stable."""

    device = UtecBleDevice(
        uid="123456",
        password="987654",
        mac_uuid="AA:BB:CC:DD:EE:FF",
        device_name="Fixture Lock",
        device_model="U-Bolt",
    )
    request = UtecBleRequest(BLECommandCode.ADMIN_LOGIN, device=device)

    assert request.package.hex() == "7f0a002040e2010006120f60a7"
    assert (
        request.encrypted_package(bytes(range(16))).hex()
        == "c7480ac089869629058d6a773e941373"
    )


@pytest.mark.asyncio
async def test_protocol_logs_exclude_credentials_packets_and_keys(caplog):
    """Debug logging exposes protocol phases, never protocol material."""

    caplog.set_level(logging.DEBUG)
    device = UtecBleDevice(
        uid="123456",
        password="987654",
        mac_uuid="AA:BB:CC:DD:EE:FF",
        device_name="Fixture Lock",
        device_model="U-Bolt",
    )
    request = UtecBleRequest(BLECommandCode.ADMIN_LOGIN, device=device)
    plain = request.package.hex()
    encrypted = request.encrypted_package(bytes(range(16))).hex()

    secret = bytes.fromhex("00112233445566778899aabbccddeeff")
    client = SimpleNamespace(read_gatt_char=lambda _uuid: None)

    async def read_gatt_char(_uuid):
        return secret

    client.read_gatt_char = read_gatt_char
    derived_key = await UtecBleDeviceKey.get_md5_key(client, device)

    logs = "\n".join(record.getMessage() for record in caplog.records)
    for sensitive in (
        "123456",
        "987654",
        "AA:BB:CC:DD:EE:FF",
        plain,
        encrypted,
        secret.hex(),
        derived_key.hex(),
    ):
        assert sensitive not in logs


def test_cloud_error_text_is_not_propagated():
    """Untrusted server messages cannot enter exceptions or logs."""

    with pytest.raises(InvalidResponse) as err:
        UtecClient._ensure_success(
            {"error": "TOKEN-SENTINEL from remote"},
            "Fixed enrollment failure",
        )

    assert str(err.value) == "Fixed enrollment failure"
    assert "TOKEN-SENTINEL" not in str(err.value)


@pytest.mark.asyncio
async def test_cloud_decode_exception_does_not_log_remote_text(caplog):
    """Remote response and exception strings stay out of API logs."""

    class BadResponse:
        async def json(self):
            raise ValueError("TOKEN-SENTINEL EMAIL-SENTINEL PIN-SENTINEL")

    caplog.set_level(logging.DEBUG)
    assert await UtecClient._response(BadResponse()) == {}
    logs = "\n".join(record.getMessage() for record in caplog.records)
    for sentinel in ("TOKEN-SENTINEL", "EMAIL-SENTINEL", "PIN-SENTINEL"):
        assert sentinel not in logs


def test_malformed_or_unknown_response_is_rejected_without_raising():
    """Truncated and unknown response frames fail closed."""

    device = UtecBleDevice(
        uid="123456",
        password="987654",
        mac_uuid="AA:BB:CC:DD:EE:FF",
        device_name="Fixture Lock",
        device_model="U-Bolt",
    )
    request = UtecBleRequest(BLECommandCode.ADMIN_LOGIN, device=device)
    response = UtecBleResponse(request, device)

    response.buffer = bytearray([0x7F, 0x00, 0x00])
    assert response.command is None
    assert response.success is False

    response.buffer = bytearray([0x7F, 0x00, 0x00, 0xFF])
    assert response.completed is True
    assert response.command is None
    assert response.is_valid is False
    assert response.success is False
