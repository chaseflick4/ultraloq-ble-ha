"""Tests for transient credential handling in the config flow."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ultraloq_ble.const import CONF_ENROLLED_DEVICES, DOMAIN
from custom_components.ultraloq_ble.enrollment import account_unique_id


async def test_user_flow_never_persists_xthings_credentials(
    hass, enrolled_u_bolt
):
    """Initial enrollment stores only minimized BLE metadata."""

    with patch(
        "custom_components.ultraloq_ble.config_flow.async_enroll_api_devices",
        return_value=[enrolled_u_bolt],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: "owner@example.com", CONF_PASSWORD: "cloud-secret"},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_ENROLLED_DEVICES: [enrolled_u_bolt]}
    assert CONF_EMAIL not in result["data"]
    assert CONF_PASSWORD not in result["data"]
    assert "owner@example.com" not in result["result"].unique_id


async def test_user_flow_reports_invalid_auth_without_logging_secret(hass):
    """Rejected credentials remain transient and return a form error."""

    from custom_components.ultraloq_ble.utecio.api import InvalidCredentials

    with patch(
        "custom_components.ultraloq_ble.config_flow.async_enroll_api_devices",
        side_effect=InvalidCredentials,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: "owner@example.com", CONF_PASSWORD: "cloud-secret"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_reconfigure_replaces_cache_without_credentials(
    hass, enrolled_u_bolt
):
    """Interactive refresh replaces only the minimized enrollment cache."""

    account = "owner@example.com"
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id=account_unique_id(account),
        data={CONF_ENROLLED_DEVICES: [{**enrolled_u_bolt, "name": "Old"}]},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.ultraloq_ble.config_flow.async_enroll_api_devices",
        return_value=[enrolled_u_bolt],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": entry.entry_id,
            },
            data=entry.data,
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: account, CONF_PASSWORD: "transient-secret"},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == {CONF_ENROLLED_DEVICES: [enrolled_u_bolt]}
    assert "transient-secret" not in repr(entry.data)


async def test_reauth_rejects_credentials_for_another_account(
    hass, enrolled_u_bolt
):
    """Reauthentication cannot replace an entry with another account's locks."""

    original = [{**enrolled_u_bolt, "name": "Original"}]
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id=account_unique_id("owner@example.com"),
        data={CONF_ENROLLED_DEVICES: original},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.ultraloq_ble.config_flow.async_enroll_api_devices",
        return_value=[enrolled_u_bolt],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data=entry.data,
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "different@example.com",
                CONF_PASSWORD: "transient-secret",
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_account"
    assert entry.data == {CONF_ENROLLED_DEVICES: original}
