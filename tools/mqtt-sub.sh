#!/usr/bin/env bash
# Subscribe to the home Mosquitto (inside the HA add-on) for a few seconds.
#   tools/mqtt-sub.sh 'victor/#' [seconds]
set -euo pipefail
PVE="${PVE:-root@192.168.31.215}"; VMID="${VMID:-105}"
topic="${1:-victor/#}"; secs="${2:-15}"
ssh -o BatchMode=yes "$PVE" "qm guest exec $VMID --timeout $((secs+20)) -- docker exec app_core_mosquitto timeout $secs mosquitto_sub -h localhost -u \"\${MQTT_USER:-mqtt}\" -P \"\${MQTT_PASS:-mqtt}\" -v -t '$topic'" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("out-data",""), end=""); e=d.get("err-data",""); print(e, file=sys.stderr) if e else None'
