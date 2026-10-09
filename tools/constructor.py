#!/usr/bin/env python3
"""Firmware Configuration Constructor for Inverter & BMS Gateways.

Generates custom ESPHome configurations for any supported inverter, BMS
(JK BMS, Daly BMS, JBD/Xiaoxiang BMS, single or parallel packs), board,
and transport mechanism (Native HA API, standard MQTT, TLS MQTT, flespi).

Usage:
  # Interactive wizard:
  python3 tools/constructor.py -i

  # Using a preset:
  python3 tools/constructor.py --preset powmr-jk-api -o esphome/my-node.yaml

  # Parallel battery packs (2x JK BMS):
  python3 tools/constructor.py --preset powmr-2xjk-api -o esphome/my-2xjk.yaml

  # Custom command line:
  python3 tools/constructor.py \
    --name my-inverter \
    --board esp32dev \
    --inverter powmr_2341 \
    --bms daly_ble \
    --transport api \
    --rules \
    -o esphome/my-inverter.yaml
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PRESETS = {
    "powmr-jk-api": {
        "description": "PowMr/Victor (Modbus 2341) + JK BMS (BLE) + Native Home Assistant API",
        "inverter": "powmr_2341",
        "bms": "jk_ble",
        "bms_packs": 1,
        "transport": "api",
        "rules": True,
    },
    "powmr-jk-mqtt": {
        "description": "PowMr/Victor (Modbus 2341) + JK BMS (BLE) + Universal MQTT",
        "inverter": "powmr_2341",
        "bms": "jk_ble",
        "bms_packs": 1,
        "transport": "mqtt",
        "rules": True,
    },
    "powmr-2xjk-api": {
        "description": "PowMr/Victor (Modbus 2341) + 2x JK BMS (Parallel Bank) + Native HA API",
        "inverter": "powmr_2341",
        "bms": "jk_ble",
        "bms_packs": 2,
        "transport": "api",
        "rules": True,
    },
    "powmr-daly-api": {
        "description": "PowMr/Victor (Modbus 2341) + Daly BMS (BLE) + Native Home Assistant API",
        "inverter": "powmr_2341",
        "bms": "daly_ble",
        "bms_packs": 1,
        "transport": "api",
        "rules": True,
    },
    "powmr-2xdaly-api": {
        "description": "PowMr/Victor (Modbus 2341) + 2x Daly BMS (Parallel Bank) + Native HA API",
        "inverter": "powmr_2341",
        "bms": "daly_ble",
        "bms_packs": 2,
        "transport": "api",
        "rules": True,
    },
    "powmr-jbd-api": {
        "description": "PowMr/Victor (Modbus 2341) + JBD / Xiaoxiang BMS (BLE) + Native Home Assistant API",
        "inverter": "powmr_2341",
        "bms": "jbd_ble",
        "bms_packs": 1,
        "transport": "api",
        "rules": True,
    },
    "powmr-2xjbd-api": {
        "description": "PowMr/Victor (Modbus 2341) + 2x JBD BMS (Parallel Bank) + Native HA API",
        "inverter": "powmr_2341",
        "bms": "jbd_ble",
        "bms_packs": 2,
        "transport": "api",
        "rules": True,
    },
    "powmr-nobms-api": {
        "description": "PowMr/Victor (Modbus 2341) - Inverter Only (No BMS) + Native HA API",
        "inverter": "powmr_2341",
        "bms": "none",
        "bms_packs": 1,
        "transport": "api",
        "rules": False,
    },
    "voltronic-jk-api": {
        "description": "Voltronic PI30 (Axpert/EASun) + JK BMS (BLE) + Native HA API",
        "inverter": "pi30",
        "bms": "jk_ble",
        "bms_packs": 1,
        "transport": "api",
        "rules": False,
    },
    "voltronic-daly-api": {
        "description": "Voltronic PI30 (Axpert/EASun) + Daly BMS (BLE) + Native HA API",
        "inverter": "pi30",
        "bms": "daly_ble",
        "bms_packs": 1,
        "transport": "api",
        "rules": False,
    },
    "voltronic-jbd-api": {
        "description": "Voltronic PI30 (Axpert/EASun) + JBD BMS (BLE) + Native HA API",
        "inverter": "pi30",
        "bms": "jbd_ble",
        "bms_packs": 1,
        "transport": "api",
        "rules": False,
    },
    "voltronic-nobms-api": {
        "description": "Voltronic PI30 (Axpert/EASun) - Inverter Only (No BMS) + Native HA API",
        "inverter": "pi30",
        "bms": "none",
        "bms_packs": 1,
        "transport": "api",
        "rules": False,
    },
    "probe-mqtt": {
        "description": "Protocol Diagnostic Scanner over MQTT",
        "inverter": "probe",
        "bms": "none",
        "bms_packs": 1,
        "transport": "mqtt",
        "rules": False,
    },
}


def build_config(
    name="solar-node",
    friendly_name=None,
    area="Solar",
    board="esp32dev",
    inverter="powmr_2341",
    inverter_tx="GPIO16",
    inverter_rx="GPIO17",
    bms="jk_ble",
    bms_packs=1,
    bms_protocol="JK02_32S",
    transport="api",
    mqtt_broker="192.168.1.100",
    mqtt_port="1883",
    mqtt_username="",
    mqtt_password="",
    mqtt_prefix=None,
    discovery_prefix="homeassistant",
    rules=False,
    temp_sensor=False,
    led_pin="GPIO2",
):
    friendly_name = friendly_name or name.replace("-", " ").title()
    mqtt_prefix = mqtt_prefix or f"{name}/node"

    # Substitutions block
    subs = {
        "node_name": name,
        "friendly_name": f'"{friendly_name}"',
        "area": f'"{area}"',
        "board": board,
        "led_pin": led_pin,
    }

    if transport == "api":
        subs["api_reboot_timeout"] = "15min"
    elif transport in ("mqtt", "mqtt_tls"):
        subs["mqtt_broker"] = f'"{mqtt_broker}"'
        subs["mqtt_port"] = f'"{mqtt_port}"'
        subs["mqtt_username"] = f'"{mqtt_username}"'
        subs["mqtt_password"] = f'"{mqtt_password}"'
        subs["mqtt_prefix"] = mqtt_prefix
        subs["discovery_prefix"] = discovery_prefix
        subs["mqtt_log_level"] = "WARN"
        subs["mqtt_reboot_timeout"] = "60min"
        if transport == "mqtt_tls":
            subs["certificate_authority"] = "!secret mqtt_ca_cert"
    elif transport == "flespi":
        subs["mqtt_prefix"] = mqtt_prefix
        subs["discovery_prefix"] = f"{name}/ha"
        subs["mqtt_log_level"] = "WARN"

    if inverter != "probe":
        subs["inverter_tx_pin"] = inverter_tx
        subs["inverter_rx_pin"] = inverter_rx
        subs["update_interval"] = "15s"

    if inverter == "powmr_2341":
        subs["inverter_voltage_offset"] = '"0"'
        subs["select_skip_updates"] = '"2"'
        subs["modbus_write_multiple"] = '"false"'

    # BMS Substitutions
    if bms == "jk_ble":
        subs["jk_bms_source"] = "github://syssi/esphome-jk-bms@59c994e726c34b123e43eb0090736fd94706f0db"
        subs["bms_protocol"] = bms_protocol
        subs["bms_throttle"] = "10s"
        if bms_packs == 2:
            subs["bms1_default_mac"] = '"00:00:00:00:00:00"'
            subs["bms2_default_mac"] = '"00:00:00:00:00:00"'
        else:
            subs["bms_default_mac"] = '"00:00:00:00:00:00"'
    elif bms == "daly_ble":
        subs["daly_bms_source"] = "github://syssi/esphome-daly-bms@ebfe3a7be3fae1e1808f3244a2d68e9b5eabf8ff"
        subs["bms_password"] = '"12345678"'
        subs["bms_status_registers"] = '"62"'
        subs["bms_throttle"] = "10s"
        if bms_packs == 2:
            subs["bms1_default_mac"] = '"00:00:00:00:00:00"'
            subs["bms2_default_mac"] = '"00:00:00:00:00:00"'
        else:
            subs["bms_default_mac"] = '"00:00:00:00:00:00"'
    elif bms == "jbd_ble":
        subs["jbd_bms_source"] = "github://syssi/esphome-jbd-bms@f70ad25b0a5bf67e29c91461ab1fccbb4ba30f58"
        subs["bms_throttle"] = "5s"
        if bms_packs == 2:
            subs["bms1_default_mac"] = '"00:00:00:00:00:00"'
            subs["bms2_default_mac"] = '"00:00:00:00:00:00"'
        else:
            subs["bms_default_mac"] = '"00:00:00:00:00:00"'

    # Packages block
    packages = [
        ("base", "packages/base.yaml"),
    ]

    if transport == "api":
        packages.append(("transport", "packages/transport-api.yaml"))
    elif transport == "mqtt":
        packages.append(("transport", "packages/transport-mqtt.yaml"))
    elif transport == "mqtt_tls":
        packages.append(("transport", "packages/transport-mqtt-tls.yaml"))
    elif transport == "flespi":
        packages.append(("mqtt", "packages/mqtt-flespi.yaml"))

    packages.append(("ota_remote", "packages/ota-remote.yaml"))
    packages.append(("status_led", "packages/status-led.yaml"))

    if inverter == "powmr_2341":
        packages.append(("inverter", "packages/inverter-powmr-2341.yaml"))
    elif inverter == "pi30":
        packages.append(("inverter", "packages/inverter-pi30.yaml"))

    # BMS Packages
    if bms != "none":
        bms_prefix = {"jk_ble": "jk", "daly_ble": "daly", "jbd_ble": "jbd"}.get(bms)
        if bms_packs == 2:
            packages.append(("bms", f"packages/bms-{bms_prefix}-ble-parallel.yaml"))
        else:
            packages.append(("bms", f"packages/bms-{bms_prefix}-ble.yaml"))

    if rules and inverter == "powmr_2341" and bms != "none":
        packages.append(("rules", "packages/rules-soc.yaml"))

    if temp_sensor:
        packages.append(("temperature", "packages/temp-ds18b20.yaml"))

    # Render YAML
    pack_desc = f"{bms} ({bms_packs} pack{'s' if bms_packs > 1 else ''})" if bms != "none" else "None"
    lines = [
        f"# {friendly_name} configuration generated by victor-node constructor",
        f"# Board: {board} | Inverter: {inverter} | BMS: {pack_desc} | Transport: {transport}",
        "#",
        "# Build: tools/build.sh <this_file.yaml>",
        "",
        "substitutions:",
    ]
    for k, v in subs.items():
        lines.append(f"  {k}: {v}")

    lines.append("")
    lines.append("packages:")
    for pkg_id, pkg_path in packages:
        lines.append(f"  {pkg_id}: !include {pkg_path}")

    lines.append("")
    return "\n".join(lines)


def interactive_wizard():
    print("==================================================")
    print("  Solar Node Configuration Constructor (Wizard)  ")
    print("==================================================")

    name = input("Node name [solar-node]: ").strip() or "solar-node"
    friendly_name = input(f"Friendly name [{name.replace('-', ' ').title()}]: ").strip() or name.replace("-", " ").title()

    print("\n1. Select Board:")
    print("  [1] ESP32 DevKit (38-pin / 30-pin, ESP32-WROOM-32 / 32U) (Recommended)")
    print("  [2] Wemos D1 Mini ESP32")
    print("  [3] ESP32-C3 DevKit")
    b_choice = input("Choice [1]: ").strip() or "1"
    board = {"1": "esp32dev", "2": "wemos_d1_mini32", "3": "esp32-c3-devkitm-1"}.get(b_choice, "esp32dev")

    print("\n2. Select Inverter:")
    print("  [1] PowMr / Victor / SmartESS (Modbus RTU 2341, 2400 baud)")
    print("  [2] Voltronic / Axpert / EASun / SP-3200 (PI30 protocol, 2400 baud)")
    print("  [3] Protocol Diagnostic Probe (Auto-sweep)")
    inv_choice = input("Choice [1]: ").strip() or "1"
    inverter = {"1": "powmr_2341", "2": "pi30", "3": "probe"}.get(inv_choice, "powmr_2341")

    inverter_tx = "GPIO16"
    inverter_rx = "GPIO17"
    if inverter != "probe":
        tx = input("Inverter RS232 TX pin (ESP32 side) [GPIO16]: ").strip()
        if tx: inverter_tx = tx
        rx = input("Inverter RS232 RX pin (ESP32 side) [GPIO17]: ").strip()
        if rx: inverter_rx = rx

    print("\n3. Battery Management System (BMS):")
    print("  Do you need battery BMS integration?")
    print("  [1] JK BMS (BLE, syssi/esphome-jk-bms) - Most popular, active balancer, 45+ sensors")
    print("  [2] Daly BMS (BLE, syssi/esphome-daly-bms) - Daly Smart BMS (Blue/standard)")
    print("  [3] JBD / Xiaoxiang BMS (BLE, syssi/esphome-jbd-bms) - Liontron / Overkill Solar / JBD")
    print("  [4] No BMS - Inverter monitoring only (standalone)")
    bms_choice = input("Choice [1]: ").strip() or "1"
    bms = {"1": "jk_ble", "2": "daly_ble", "3": "jbd_ble", "4": "none"}.get(bms_choice, "jk_ble")

    bms_packs = 1
    bms_protocol = "JK02_32S"
    if bms != "none":
        print("\n  Battery Bank Configuration (Parallel Packs):")
        print("    [1] Single battery pack (1 BMS)")
        print("    [2] 2 parallel battery packs (2 BMSs with bank aggregation & SoC delta warning)")
        p_choice = input("  Choice [1]: ").strip() or "1"
        bms_packs = 2 if p_choice == "2" else 1

        if bms == "jk_ble":
            print("\n  Select JK BMS Hardware / Protocol Version:")
            print("    [1] JK02_32S (Recommended: HW 11.x and newer, 24S / 32S boards, PB-series)")
            print("    [2] JK02_24S (Legacy: HW version < 11.x, older 24S boards)")
            bp_choice = input("  Choice [1]: ").strip() or "1"
            bms_protocol = "JK02_24S" if bp_choice == "2" else "JK02_32S"

    print("\n4. Select Transport / Communication:")
    print("  [1] Native Home Assistant API (Direct connection, auto-discovered, NO broker required!)")
    print("  [2] Standard MQTT (Local Mosquitto, EMQX, HiveMQ, etc. port 1883)")
    print("  [3] MQTT over TLS (Cloud broker or custom TLS broker, port 8883)")
    print("  [4] flespi MQTT (Cloud TLS bridge for remote sites behind CGNAT)")
    t_choice = input("Choice [1]: ").strip() or "1"
    transport = {"1": "api", "2": "mqtt", "3": "mqtt_tls", "4": "flespi"}.get(t_choice, "api")

    mqtt_broker = "192.168.1.100"
    mqtt_port = "1883"
    mqtt_username = ""
    mqtt_password = ""
    if transport in ("mqtt", "mqtt_tls"):
        mqtt_broker = input("MQTT Broker host/IP [192.168.1.100]: ").strip() or "192.168.1.100"
        default_port = "8883" if transport == "mqtt_tls" else "1883"
        mqtt_port = input(f"MQTT Port [{default_port}]: ").strip() or default_port
        mqtt_username = input("MQTT Username (optional): ").strip()
        mqtt_password = input("MQTT Password (optional): ").strip()

    rules = False
    if inverter == "powmr_2341" and bms != "none":
        r_choice = input("\nEnable autonomous battery SOC rules on device? [Y/n]: ").strip().lower()
        rules = (r_choice != "n")

    temp_sensor = input("\nInclude DS18B20 temperature sensor on GPIO4? [y/N]: ").strip().lower() == "y"

    out_file = input(f"\nOutput file path [esphome/{name}.yaml]: ").strip() or f"esphome/{name}.yaml"
    out_path = Path(out_file)
    if not out_path.is_absolute():
        out_path = ROOT / out_file

    config_str = build_config(
        name=name,
        friendly_name=friendly_name,
        board=board,
        inverter=inverter,
        inverter_tx=inverter_tx,
        inverter_rx=inverter_rx,
        bms=bms,
        bms_packs=bms_packs,
        bms_protocol=bms_protocol,
        transport=transport,
        mqtt_broker=mqtt_broker,
        mqtt_port=mqtt_port,
        mqtt_username=mqtt_username,
        mqtt_password=mqtt_password,
        rules=rules,
        temp_sensor=temp_sensor,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(config_str)
    print(f"\n[+] Config successfully generated at: {out_path}")
    print(f"    Build with: tools/build.sh {out_path.name}")


def main():
    parser = argparse.ArgumentParser(description="Inverter & BMS Firmware Constructor")
    parser.add_argument("-i", "--interactive", action="store_true", help="Launch interactive wizard")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), help="Load a pre-defined preset")
    parser.add_argument("--name", default="solar-node", help="Node name (default: solar-node)")
    parser.add_argument("--friendly-name", help="Friendly name (default: Solar Node)")
    parser.add_argument("--area", default="Solar", help="Home Assistant area (default: Solar)")
    parser.add_argument("--board", default="esp32dev", choices=["esp32dev", "wemos_d1_mini32", "esp32-c3-devkitm-1"], help="ESP32 board")
    parser.add_argument("--inverter", default="powmr_2341", choices=["powmr_2341", "pi30", "probe"], help="Inverter type")
    parser.add_argument("--inverter-tx", default="GPIO16", help="TX pin (default: GPIO16)")
    parser.add_argument("--inverter-rx", default="GPIO17", help="RX pin (default: GPIO17)")
    parser.add_argument("--bms", default="jk_ble", choices=["jk_ble", "daly_ble", "jbd_ble", "none"], help="BMS type")
    parser.add_argument("--bms-packs", type=int, default=1, choices=[1, 2], help="Number of battery packs (1 or 2 parallel packs)")
    parser.add_argument("--bms-protocol", default="JK02_32S", choices=["JK02_32S", "JK02_24S"], help="JK BMS protocol")
    parser.add_argument("--transport", default="api", choices=["api", "mqtt", "mqtt_tls", "flespi"], help="Transport")
    parser.add_argument("--mqtt-broker", default="192.168.1.100", help="MQTT broker host")
    parser.add_argument("--mqtt-port", default="1883", help="MQTT broker port")
    parser.add_argument("--mqtt-username", default="", help="MQTT username")
    parser.add_argument("--mqtt-password", default="", help="MQTT password")
    parser.add_argument("--rules", action="store_true", help="Enable autonomous SOC rules")
    parser.add_argument("--no-rules", action="store_true", help="Disable autonomous SOC rules")
    parser.add_argument("--temp-sensor", action="store_true", help="Include DS18B20 on GPIO4")
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")

    args = parser.parse_args()

    if args.interactive or len(sys.argv) == 1:
        interactive_wizard()
        return

    # Preset overrides
    rules = args.rules
    inverter = args.inverter
    bms = args.bms
    bms_packs = args.bms_packs
    transport = args.transport

    if args.preset:
        preset_data = PRESETS[args.preset]
        inverter = preset_data["inverter"]
        bms = preset_data["bms"]
        bms_packs = preset_data.get("bms_packs", 1)
        transport = preset_data["transport"]
        rules = preset_data["rules"]

    if args.no_rules:
        rules = False

    config_str = build_config(
        name=args.name,
        friendly_name=args.friendly_name,
        area=args.area,
        board=args.board,
        inverter=inverter,
        inverter_tx=args.inverter_tx,
        inverter_rx=args.inverter_rx,
        bms=bms,
        bms_packs=bms_packs,
        bms_protocol=args.bms_protocol,
        transport=transport,
        mqtt_broker=args.mqtt_broker,
        mqtt_port=args.mqtt_port,
        mqtt_username=args.mqtt_username,
        mqtt_password=args.mqtt_password,
        rules=rules,
        temp_sensor=args.temp_sensor,
    )

    if args.output:
        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = ROOT / args.output
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(config_str)
        print(f"[+] Configuration written to {out_path}")
    else:
        print(config_str)


if __name__ == "__main__":
    main()
