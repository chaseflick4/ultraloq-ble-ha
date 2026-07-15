<h1 align="center">Ultraloq BLE</h1>

<p align="center"><b>Control your Bluetooth capable U-Tec locks locally and natively in Home Assistant.</b>
</p>

---

This hardening work is based on [inventor7777/ultraloq-ble-ha](https://github.com/inventor7777/ultraloq-ble-ha), itself [forked from maeneak/utecio-ha](https://github.com/maeneak/utecio-ha). The original MIT license and attribution are preserved.

I really wanted to have local control over my U-Bolt Pro locks, and the original integration wouldn't even start the config process. So I forked it and fixed the biggest bugs, then did extensive testing and iterating with the help of Codex. In addtion to extending lock support, autolock status and battery level are now first class sensors instead of being buried in the attributes. This integration should have all of the original features *(plus first class sensors)* for non U-Bolt Pro locks, *plus* full support for the U-Bolt Pro locks.

## Requirements
- Active (GATT) Bluetooth support in Home Assistant, whether through [your host's built in Bluetooth](https://www.home-assistant.io/integrations/bluetooth/), a [local USB adapter](https://a.co/d/09RioHgV), or an [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy/).
- Internet access during initial enrollment, and again only when the user explicitly refreshes enrollment.

## Features

Entities currently exposed per lock:
- `lock`
- `sensor.battery_level`
- `sensor`
- `sensor.lock_mode`
- `sensor.bolt_status` when the model reports meaningful bolt status. U-Bolt Pros do not.
- `number.autolock_time`

Important Bluetooth note:
- Passive advertisement-only proxies are not enough for lock control
- Shelly Bluetooth proxy sightings can help discovery, but active GATT connectivity is what actually matters for operating the lock
- If HA decides that the advertisement is not connectable, it will cause status updates and lock controls to fail

## Install
> **Hardening branch:** Until these changes are merged and released upstream, the HACS badge below installs the upstream release, not this branch. To evaluate the hardening branch, use the manual installation steps with files checked out from `hardening/security-ha-2026.7.2`.

You can install using HACS:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=inventor7777&repository=ultraloq-ble-ha&category=integration)

Or manually:
1. Open your Home Assistant config directory.
1. Create `custom_components` if it does not already exist.
1. Copy the `custom_components/ultraloq_ble/` folder from this repository into your Home Assistant config directory.
1. Restart Home Assistant.

## Notes

### Speed and Reliability
This integration relies on a direct, active BLE connection to the lock. Ultraloq locks are VERY stingy about BLE connections, even with the offical WiFi bridge. This means that updates may fail, and the update speed will be much lower than a normal Zigbee/WiFi lock. 

### Offline-ish Behavior

This integration uses cloud-assisted enrollment only when needed:
- first setup
- an explicit **Reconfigure** action to refresh local BLE metadata

Normal operation such as:
- lock
- unlock
- state updates
- reading battery/autolock/mode values
- setting the auto-lock timer

is intended to happen locally over BLE.

The Xthings email and account password are used transiently during enrollment and are not retained. Home Assistant stores only the minimum per-lock BLE metadata needed for unattended local control, including the BLE UID and admin credential. Treat Home Assistant storage and backups as sensitive.

### Private Xthings endpoint dependency

Enrollment currently uses undocumented U-tec mobile-app endpoints under `uemc.u-tec.com/app/` and `cloud.u-tec.com/app/`. These endpoints can change without notice. Normal lock control and status reads do not use them after enrollment.

The documented [Xthings OpenAPI Discovery API](https://developer.xthings.com/hc/en-us/articles/39867633454361-Developer-Foundational-APIs) is not currently a drop-in replacement: its public schema does not provide the per-lock BLE UID, BLE admin credential, raw connectable address, or optional wake-receiver address this protocol needs. OpenAPI OAuth would replace an account password with persistent access/refresh tokens, but it does not solve the missing BLE enrollment fields. If Xthings publishes a supported BLE enrollment API, this dependency should be revisited.

### Security and diagnostics

- Integration-owned debug logs omit account credentials, BLE admin credentials, UIDs, Bluetooth addresses, serial numbers, packets, and cryptographic material. Home Assistant's Bluetooth stack and adapter libraries may still identify Bluetooth devices while troubleshooting transport.
- Diagnostics are allowlist-only and exclude lock/account identifiers and authentication material.
- Before sharing any support artifact, review it for private data.
- Do not use real credentials or lock packet captures as test fixtures.

### Home Assistant compatibility

The automated suite targets Home Assistant Core 2026.7.2 and covers enrollment/config migration, diagnostics redaction, protocol/crypto fixtures, U-Bolt model mapping, Bluetooth adapter selection, and entity state transitions. A physical lock remains required for the supervised checks in [the real-lock test plan](docs/supervised-real-lock-test-plan.md).

### Sensors

Each lock may expose:
- `Battery Level`
- `Autolock Time`
- `Lock Mode`
- `Bolt Status`

Notes:
- `Bolt Status` is skipped for models where it is known to be useless or always unavailable
- `Autolock Time` is exposed as a duration sensor in seconds

### Known Limitations

- Bluetooth quality matters a lot. Weak or non-connectable advertisements will cause timeouts or unavailable entities. You will need active-capable Bluetooth nodes very close to each lock.
- Some lock models may still need extra command or capability tuning.
- The integration exposes the raw autolock controls. The lock seems to discard some seconds inputs, if I could find all of the accepted inputs we could add a proper selector.
- State updates after a lock or unlock are very slow and dependent on refresh interval. Perhaps there is a way to subscribe to Ultraloq BLE pushes, but I do not have the tools to reverse engineer such a thing.
- Shelly Bluetooth proxies are incapable of starting an active GATT BLE connection, so you will need either a USB Bluetooth adapter or an ESPHome device with `active: true` enabled in the Bluetooth configuration.
- There is a Bleak depreciation warning in the debug logs. I am aware of this but I'd like to get the rest of the implementation stable before attacking that.
- Some locks randomly go offline due to them not responding to `ADMIN_LOGIN`. I am working on a fix, but it only happens occasionally.

### Lock shows up but will not operate

Check:
- the lock is in Bluetooth range
- your Home Assistant Bluetooth adapter or ESPHome proxy can make active connections
- the lock is not only being seen as `connectable: false`
- Unsupported device, in which case you could try reporting an issue here

*Full disclaimer: Most of the improvements from the original were by GPT 5.4 Codex. However, I personally use this integration and I am happy with it, so I am sharing it in case it could be useful to anyone else.*
