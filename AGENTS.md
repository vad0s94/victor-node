# AGENTS.md — victor-node

Instructions for any coding agent (Codex, Antigravity/Gemini, Claude Code) working in this repo.
Current state and next steps: **docs/STATUS.md** (read it first). Human docs: README.md, docs/*.md (Ukrainian).

## What this is
Modular ESPHome firmware + Home Assistant config to monitor and control off-grid and hybrid solar installations:
- Inverters: **PowMr / Victor** (POW-HVM series, Modbus RTU 2341, 2400 8N1, slave 5), **Voltronic** (Axpert / EASun / SP-3200, PI30 protocol), and **Probe** (diagnostic protocol scanner).
- Battery: **JK BMS** (JK-B1A24S15P / JK-B2A..., HW 11.x, over BLE `JK02_32S` or `JK02_24S`), or standalone (no BMS).
- Connectivity: **Native Home Assistant API** (for local LAN / WireGuard, zero broker needed), **Universal MQTT** (for any local or cloud broker), or **MQTT with TLS & Bridge** (e.g. flespi, HiveMQ Cloud, EMQX, AWS IoT) for remote sites behind CGNAT.
- Node hardware: ESP32-WROOM-32 / 32U, Wemos D1 Mini ESP32, ESP32-C3.
- Automation: on-device battery protection and charge current rules (`packages/rules-soc.yaml`) running autonomously on ESP32 without internet.

## Rules the owner set
1. **Open source first**, own code only where nothing exists. Pin upstream to commits, credit it in README/NOTICE.
2. Human-facing docs in **Ukrainian**; code, comments and commit messages in English.
3. Do not commit or push unless the owner asks. Never put secrets in git (`esphome/secrets.yaml` is ignored).
4. Inverter settings live in EEPROM: never write in tight loops; write only when the value differs; rules keep a 5 min per-setting gap.
5. Don't run anything that changes the home HA (bridge install, add-on restart, file writes) without the owner's explicit go-ahead. A Mosquitto restart drops every MQTT device at home for ~10 s.
6. The person on site may be non-technical: anything they must do goes into docs/onsite-uk.md, in plain Ukrainian.

## Layout
```
esphome/
  victor.yaml           production node: Modbus 2341 + JK BMS + rules + flespi
  victor-pi30.yaml      Voltronic PI30 test / deployment profile
  victor-probe.yaml     protocol finder (Travis90x sweep), logs over MQTT
  powmr-jk-api.yaml     open preset: PowMr + JK BMS + Native HA API
  powmr-jk-mqtt.yaml    open preset: PowMr + JK BMS + Universal MQTT
  powmr-nobms-api.yaml  open preset: PowMr + No BMS + Native HA API
  voltronic-jk-api.yaml open preset: Voltronic PI30 + JK BMS + Native HA API
  voltronic-nobms-api.yaml open preset: Voltronic PI30 + No BMS + Native HA API
  packages/             base, transport-api, transport-mqtt, transport-mqtt-tls, mqtt-flespi,
                        ota-remote, status-led, inverter-powmr-2341, inverter-pi30,
                        bms-jk-ble, rules-soc, temp-ds18b20
  vendor/aver-ua/       aver-ua/esphome-hybrid-inverter-2341 @9c607d6 + patch
  secrets.example.yaml  copy to secrets.yaml
mosquitto/
  bridge-universal.conf.example   universal broker bridge template (HiveMQ, EMQX, flespi, VPS)
  flespi-bridge.conf              owner's flespi bridge config
homeassistant/
  packages/victor.yaml            notifications package
  dashboards/solar.yaml           dashboard (sunsynk-power-flow-card, jk-bms-card)
tools/
  constructor.py        interactive wizard & CLI configuration generator
  build.sh              cross-platform build script (.factory.bin, .ota.bin, .md5)
  fetch-refs.sh         downloads .venv and vendor reference tarballs
  check-entities.py     verifies entity ids between firmware and HA dashboard
.github/workflows/
  ci.yml                validates configs, constructor presets, and entity parity
  release.yml           builds matrix of release firmwares on tag push
  build-custom.yml      on-demand browser custom firmware builder (workflow_dispatch)
docs/                   hardware, mqtt-bridges, bridge, firmware, home-test, home-assistant, onsite-uk, runbook, STATUS
```

## Commands
```bash
tools/fetch-refs.sh                                   # once: .venv + tools/ref/ (JK tarball)
cp esphome/secrets.example.yaml esphome/secrets.yaml  # fill in (dummy values work for building)

# Generate custom firmware configuration:
python3 tools/constructor.py -i                       # interactive wizard
python3 tools/constructor.py --preset powmr-jk-api -o esphome/my-node.yaml

# Build firmware image:
JK_BMS_SOURCE=../tools/ref/jk-src/components tools/build.sh powmr-jk-api.yaml

# Entity id validation:
.venv/bin/python tools/check-entities.py victor.yaml
```

## Conventions that other parts depend on
- MQTT nodes: `discovery_object_id_generator: device_name` → HA entity ids `<domain>.<node_name>_<snake_case name>`.
- Transport abstraction: `base.yaml` declares `globals: transport_connected`. Transports (`transport-api.yaml`, `transport-mqtt.yaml`, `mqtt-flespi.yaml`) update this flag; `status-led.yaml` observes it.
- Browser web flashing: `base.yaml` enables `improv_serial:` and `captive_portal:` for web.esphome.io compatibility.
