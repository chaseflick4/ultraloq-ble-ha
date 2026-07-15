# Supervised original U-Bolt validation plan

Target: original Bluetooth U-Bolt, Home Assistant OS 2026.7.2, and either a local Bluetooth adapter or an active ESPHome Bluetooth proxy.

This plan is intentionally gated. Automated tests never contact a lock. Do not run an unlock operation unattended.

## Safety gates

1. Have a person at the door, an alternate entry method, and fresh lock batteries.
2. Disable automations and voice assistants that can call this lock entity.
3. Back up Home Assistant before installing the custom integration.
4. Review logs before sharing them. Never publish Xthings credentials, the BLE admin credential/PIN, UID, token, key material, packet bytes, serial number, or Bluetooth address.
5. Stop if the reported state disagrees with the physical bolt.

## Install and enrollment

1. Install this branch as a custom integration and restart Home Assistant OS 2026.7.2.
2. Confirm the Bluetooth adapter or ESPHome proxy is active-connection capable. For ESPHome, `bluetooth_proxy.active` must be enabled.
3. Add Ultraloq BLE and enter the Xthings credentials interactively.
4. Inspect the resulting config entry in a backup or controlled development copy: it should contain `enrolled_devices` but no Xthings `email`, `password`, token, raw address/room response, or serial number.
5. Restart Home Assistant with Internet access disabled and confirm the entry still loads from cached enrollment.

## Read-only compatibility gate

Perform these checks repeatedly before any write:

1. Confirm Home Assistant resolves a `connectable: true` path.
2. Read lock status, battery, work mode, mute state, and auto-lock time.
3. Repeat at least ten polling cycles and record success/failure counts and latency without recording identifiers or packet data.
4. Restart Home Assistant and the ESPHome proxy separately, then repeat the reads.
5. Test with the phone app closed, then open, to identify BLE connection contention.

Proceed only if authenticated reads are repeatable and Home Assistant state matches the physical lock.

## Supervised write gate

With a person physically present:

1. Start with the door open and the bolt able to move freely.
2. Issue one **lock** command from Home Assistant. Confirm the physical bolt, Home Assistant state, and U-tec app state.
3. Issue one **unlock** command while the observer remains at the door with an alternate entry method. Confirm all three states again.
4. Do not schedule, automate, script, or remotely trigger the unlock test.
5. If auto-lock is enabled, verify Home Assistant polls after the interval rather than assuming the bolt locked.

## Failure recovery

Supervise each case and avoid unlock automation:

- lock busy because the phone app is connected;
- weak signal or proxy restart during a read;
- Home Assistant restart during an idle period;
- rejected admin login;
- jammed bolt during a lock command;
- low batteries.

Expected behavior: errors are visible to the Home Assistant caller, transitional states clear, diagnostics contain no identifiers or secrets, and no timer invents a locked state without a real status response.

## Evidence boundary

Passing the repository tests proves config, redaction, protocol fixtures, model mapping, adapter selection, and entity-state logic against synthetic data and Home Assistant 2026.7.2. Only the supervised steps above can establish compatibility with this specific lock, firmware, radio environment, and ESPHome proxy.
