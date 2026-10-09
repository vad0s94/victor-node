#!/usr/bin/env bash
# Installs mosquitto/flespi-bridge.conf into Home Assistant and turns on the
# Mosquitto add-on "customize" option, then restarts the add-on (~10 s outage
# for every MQTT device at home: Zigbee2MQTT, JK gateway, Solar2MQTT).
#
# Runs from this Mac through the Proxmox host (HA is VM 105 there).
# The flespi "home-bridge" token is read from the terminal, never echoed or stored locally.
#   tools/ha-enable-bridge.sh
set -euo pipefail

PVE="${PVE:-root@192.168.31.215}"
VMID="${VMID:-105}"
here="$(cd "$(dirname "$0")/.." && pwd)"

read -r -s -p "flespi home-bridge token: " TOKEN; echo
[ ${#TOKEN} -ge 32 ] || { echo "token looks too short" >&2; exit 1; }

conf=$(sed "s|HOME_BRIDGE_TOKEN|${TOKEN}|" "$here/mosquitto/flespi-bridge.conf" | base64)

# 1. write /share/mosquitto/flespi-bridge.conf (HAOS host path /mnt/data/supervisor/share)
ssh -o BatchMode=yes "$PVE" "qm guest exec $VMID --pass-stdin 1 -- sh -c 'mkdir -p /mnt/data/supervisor/share/mosquitto && base64 -d > /mnt/data/supervisor/share/mosquitto/flespi-bridge.conf && chmod 600 /mnt/data/supervisor/share/mosquitto/flespi-bridge.conf'" <<<"$conf" >/dev/null

# 2. customize.active = true via the Supervisor API, 3. restart the add-on.
#    Runs inside the homeassistant container: it has python and SUPERVISOR_TOKEN.
api_py=$(base64 <<'PY'
import json, os, urllib.request
base = "http://supervisor/addons/core_mosquitto"
hdr = {"Authorization": "Bearer " + os.environ["SUPERVISOR_TOKEN"], "Content-Type": "application/json"}
def call(path, data=None):
    req = urllib.request.Request(base + path, data=json.dumps(data).encode() if data is not None else None,
                                 headers=hdr, method="POST" if data is not None else "GET")
    return json.load(urllib.request.urlopen(req, timeout=60))
opts = call("/info")["data"]["options"]
opts["customize"] = {"active": True, "folder": "mosquitto"}
call("/options", {"options": opts})
call("/restart", {})
print("mosquitto restarted with customize.active=true")
PY
)
ssh -o BatchMode=yes "$PVE" "qm guest exec $VMID --timeout 90 --pass-stdin 1 -- sh -c 'base64 -d > /tmp/enable_bridge.py && docker exec -i homeassistant python3 - < /tmp/enable_bridge.py; rm -f /tmp/enable_bridge.py'" <<<"$api_py" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print((d.get("out-data","") + d.get("err-data","")).strip())'

echo "Bridge installed. Check: tools/mqtt-sub.sh 'victor/bridge/state'  (expect 1)"
