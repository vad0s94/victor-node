# AGENTS.md — victor-node

Instructions for any coding agent (Codex, Antigravity/Gemini, Claude Code) working in this repo.
Current state and next steps: **docs/STATUS.md** (read it first). Human docs: README.md, docs/*.md (Ukrainian).

## What this is
ESPHome firmware + Home Assistant config to monitor and control a remote off-grid site ~300 km away:
- Inverter **Victor NM-ECO-6.2KW PLUS** (48 V, PowMr POW-HVM platform) over RS232 RJ45, most likely **Modbus RTU protocol 2341** (2400 8N1, slave 5). Not yet confirmed on the real unit.
- Battery with **JK BMS JK-B1A24S15P**, HW 11.x, over Bluetooth (`JK02_32S`).
- Node: ESP32-WROOM-32U (external antenna). Spare: Wemos D1 Mini ESP32.
- Link: Wi-Fi at the site → **flespi MQTT (TLS 8883)** → Mosquitto bridge in the owner's home HA (home is behind CGNAT; no inbound connections possible).
- Home HA: HAOS VM 105 on Proxmox `root@192.168.31.215`, reached with `qm guest exec 105 ...` (no HA token needed). Mosquitto add-on `core_mosquitto`, local login `mqtt/mqtt`.

## Rules the owner set
1. **Open source first**, own code only where nothing exists. Pin upstream to commits, credit it in README/NOTICE.
2. Human-facing docs in **Ukrainian**; code, comments and commit messages in English.
3. Do not commit or push unless the owner asks. Never put secrets in git (`esphome/secrets.yaml` is ignored).
4. Inverter settings live in EEPROM: never write in tight loops; write only when the value differs; rules keep a 5 min per-setting gap.
5. Don't run anything that changes the home HA (bridge install, add-on restart, file writes) without the owner's explicit go-ahead. A Mosquitto restart drops every MQTT device at home for ~10 s.
6. The relative on site is non-technical: anything they must do goes into docs/onsite-uk.md, in plain Ukrainian.

## Layout
```
esphome/
  victor.yaml           remote node: Modbus 2341 + JK BMS + on-device rules   <- ships to the site
  victor-pi30.yaml      same node for the owner's home SP-3200 (PI30) - prototype/test
  victor-probe.yaml     protocol finder (Travis90x sweep), logs over MQTT
  packages/             base, mqtt-flespi (inline CA), ota-remote, status-led,
                        inverter-powmr-2341, inverter-pi30, bms-jk-ble, rules-soc, temp-ds18b20
  vendor/aver-ua/       aver-ua/esphome-hybrid-inverter-2341 @9c607d6 + esphome-2026.9.patch (see NOTICE.md)
  certs/flespi-ca.pem   GlobalSign R6 + R1 (reference copy of the CA inlined in mqtt-flespi.yaml)
  secrets.example.yaml  copy to secrets.yaml
mosquitto/flespi-bridge.conf     bridge template (token placeholder HOME_BRIDGE_TOKEN)
homeassistant/packages/victor.yaml       notifications (Ukrainian)
homeassistant/dashboards/dacha.yaml      dashboard "Дача" (sunsynk-power-flow-card, jk-bms-card)
tools/   fetch-refs.sh, build.sh, check-entities.py, ha-enable-bridge.sh, ota-remote.sh,
         mqtt-sub.sh, mqtt-log.sh, update-flespi-ca.sh
docs/    hardware, bridge, firmware, home-test, home-assistant, onsite-uk, runbook, STATUS
```

## Commands
```bash
tools/fetch-refs.sh                                   # once: .venv (ESPHome 2026.9.1) + tools/ref/ (JK tarball, upstream refs)
cp esphome/secrets.example.yaml esphome/secrets.yaml  # fill in (owner's secrets; dummies are fine for compiling)
JK_BMS_SOURCE=../tools/ref/jk-src/components tools/build.sh victor.yaml       # -> esphome/build/victor.{factory,ota}.bin
(cd esphome && ../.venv/bin/esphome -s jk_bms_source ../tools/ref/jk-src/components config victor.yaml)   # validate only
.venv/bin/python tools/check-entities.py victor.yaml  # dashboard/package entity ids exist in firmware
```
`JK_BMS_SOURCE` points the JK external component at the local tarball; without it ESPHome git-clones
`github://syssi/esphome-jk-bms@59c994e...`, which works but is very slow from the owner's network.
All three firmwares share build dir `.esphome/build/victor` (same node name), so switching configs rebuilds fully (~2-5 min).

## Conventions that other parts depend on
- Node name `victor`, friendly `Victor`, area `Дача`. MQTT `topic_prefix: victor/node`, `discovery_prefix: victor/ha`,
  `discovery_object_id_generator: device_name` → HA entity ids `<domain>.victor_<snake_case name>`.
  Renaming an entity breaks the dashboard/package: run `tools/check-entities.py` after any rename.
- flespi tokens: `victor-node` (firmware, `flespi_token`) and `home-bridge` (Mosquitto bridge), both ACL `victor/#`.
- Inverter entities come from the aver-ua package (ids like `utility_charge_current`, `output_source_priority_select`,
  `charger_source_priority_select`, `grid_active`, `load_power`, `pv_power`); `packages/rules-soc.yaml` uses these ids.
- BMS entities: syssi default keys with a `BMS ` name prefix (jk-bms-card prefix `victor_bms`). All 45 writable
  numbers and 17 switches are exposed; the `shutdown` button is deliberately omitted (can't be undone remotely).
- `packages/base.yaml`: Wi-Fi `reboot_timeout: 0s` on purpose (rules must keep running without Wi-Fi).

## Known caveats
- Upstream aver-ua uses options ESPHome 2026.9 ignores or deprecates (`skip_updates`, `command_throttle`,
  `force_new_range`): warnings only; they stop working in 2027.2/2027.3 — patch the vendored copy then.
- Static RAM of victor.yaml is 87 % (BLE + TLS + web_server + ~270 entities). Check the "Heap Free" /
  "Heap Min Free" sensors on real hardware; if heap gets low, drop `web_server` or BMS cell-resistance sensors first.
- Entity ids are predicted, not yet observed in HA (newer HA may prefer `default_entity_id` over `object_id`).
- `tools/ha-enable-bridge.sh` and `tools/ota-remote.sh` are untested against the live HA (it was unreachable when written).
