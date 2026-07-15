"""Tests for removing legacy persistent cloud credentials."""

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ultraloq_ble import async_migrate_entry
from custom_components.ultraloq_ble.const import (
    CONF_API_DEVICES,
    CONF_ENROLLED_DEVICES,
    DOMAIN,
)


async def test_migration_normalizes_cache_and_removes_credentials(
    hass, raw_u_bolt_device
):
    """A populated legacy cache migrates without another cloud request."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        unique_id="owner@example.com",
        data={
            CONF_EMAIL: "owner@example.com",
            CONF_PASSWORD: "cloud-secret",
            CONF_API_DEVICES: [raw_u_bolt_device],
        },
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry)
    assert entry.version == 2
    assert set(entry.data) == {CONF_ENROLLED_DEVICES}
    assert entry.data[CONF_ENROLLED_DEVICES][0]["admin_pin"] == "1234"
    serialized = repr(entry.data)
    for secret in (
        "cloud-secret",
        "owner@example.com",
        "SERIAL-MUST-NOT-PERSIST",
        "TOKEN-MUST-NOT-PERSIST",
        "REMOTE-MUST-NOT-PERSIST",
    ):
        assert secret not in serialized
