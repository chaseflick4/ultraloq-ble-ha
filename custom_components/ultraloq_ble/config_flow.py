"""Config flow for Ultraloq BLE integration."""
from __future__ import annotations

from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ENROLLED_DEVICES,
    CONF_STAGGER_DELAY,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STAGGER_DELAY,
    DOMAIN,
    LOGGER,
)
from .enrollment import account_unique_id
from .util import InvalidCredentials, NoDevicesError, async_enroll_api_devices

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


class UltraloqConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ultraloq integration."""

    VERSION = 2

    entry: config_entries.ConfigEntry | None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> UltraloqOptionsFlowHandler:
        """Get the options flow for this handler."""
        return UltraloqOptionsFlowHandler(config_entry)

    async def _async_enroll(
        self, user_input: dict[str, Any]
    ) -> tuple[list[dict[str, str]] | None, dict[str, str]]:
        """Use Xthings credentials once and return minimized BLE metadata."""

        try:
            devices = await async_enroll_api_devices(
                self.hass,
                user_input[CONF_EMAIL],
                user_input[CONF_PASSWORD],
            )
        except ConnectionError:
            return None, {"base": "cannot_connect"}
        except NoDevicesError:
            return None, {"base": "no_locks"}
        except InvalidCredentials:
            return None, {"base": "invalid_auth"}
        except Exception as err:
            LOGGER.error(
                "Unexpected error during Ultraloq enrollment (%s)",
                type(err).__name__,
            )
            return None, {"base": "cannot_connect"}
        return devices, {}

    async def async_step_reauth(
        self, _entry_data: dict[str, Any]
    ) -> FlowResult:
        """Handle explicit cloud-assisted re-enrollment."""

        self.entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm re-authentication with Utec."""

        errors: dict[str, str] = {}

        if user_input is not None:
            devices, errors = await self._async_enroll(user_input)
            if devices is not None:
                assert self.entry is not None
                account_id = account_unique_id(user_input[CONF_EMAIL])
                await self.async_set_unique_id(account_id)
                self._abort_if_unique_id_mismatch(reason="wrong_account")
                return self.async_update_and_abort(
                    self.entry,
                    unique_id=account_id,
                    data={CONF_ENROLLED_DEVICES: devices},
                    reason="reauth_successful",
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Refresh cached BLE enrollment without retaining cloud credentials."""

        errors: dict[str, str] = {}
        if user_input is not None:
            devices, errors = await self._async_enroll(user_input)
            if devices is not None:
                account_id = account_unique_id(user_input[CONF_EMAIL])
                await self.async_set_unique_id(account_id)
                self._abort_if_unique_id_mismatch(reason="wrong_account")
                return self.async_update_and_abort(
                    self._get_reconfigure_entry(),
                    unique_id=account_id,
                    data={CONF_ENROLLED_DEVICES: devices},
                    reason="reconfigure_successful",
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}

        if user_input is not None:
            devices, errors = await self._async_enroll(user_input)
            if devices is not None:
                await self.async_set_unique_id(
                    account_unique_id(user_input[CONF_EMAIL])
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data={CONF_ENROLLED_DEVICES: devices},
                    options={
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                        CONF_STAGGER_DELAY: DEFAULT_STAGGER_DELAY,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )


class UltraloqOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Ultraloq options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self._config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=1)),
            vol.Optional(
                CONF_STAGGER_DELAY,
                default=self._config_entry.options.get(
                    CONF_STAGGER_DELAY, DEFAULT_STAGGER_DELAY
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=0)),
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))
