#!/usr/bin/env bash
# Remote firmware update of the Victor node through Home Assistant + flespi.
#
#   HA_PUBLIC_URL=https://ha.example.com tools/ota-remote.sh [esphome/build/victor.ota.bin]
#   tools/ota-remote.sh --cleanup        # remove uploaded images after the update
#
# 1. Uploads the image to HA's /config/www/victor-ota/<random>/ (served at
#    $HA_PUBLIC_URL/local/... over the existing cloudflared tunnel; the random
#    path keeps it unguessable, --cleanup deletes it afterwards).
# 2. Sets the node's "OTA URL" and "OTA MD5" text entities and presses
#    "Flash Firmware From URL" via MQTT; the bridge carries it to the node.
# The image embeds Wi-Fi and flespi secrets: always run --cleanup when done.
set -euo pipefail

PVE="${PVE:-root@192.168.31.215}"; VMID="${VMID:-105}"
MQTT_USER="${MQTT_USER:-mqtt}"; MQTT_PASS="${MQTT_PASS:-mqtt}"
WWW=/mnt/data/supervisor/homeassistant/www/victor-ota
here="$(cd "$(dirname "$0")/.." && pwd)"

guest() {  # run a shell command inside the HAOS VM, print its stdout
  ssh -o BatchMode=yes "$PVE" "qm guest exec $VMID --timeout 60 $2 -- sh -c '$1'" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); sys.stdout.write(d.get("out-data","")); sys.stderr.write(d.get("err-data",""))'
}

if [ "${1:-}" = "--cleanup" ]; then
  guest "rm -rf $WWW && echo removed $WWW" ""
  exit 0
fi

: "${HA_PUBLIC_URL:?set HA_PUBLIC_URL, e.g. https://ha.example.com}"
fw="${1:-$here/esphome/build/victor.ota.bin}"
[ -f "$fw" ] || { echo "no firmware at $fw (run tools/build.sh first)" >&2; exit 1; }
md5=$(md5 -q "$fw")
dir=$(openssl rand -hex 16)

echo "uploading $(basename "$fw") ($(wc -c <"$fw") bytes, md5 $md5)"
guest "mkdir -p $WWW/$dir && : > $WWW/$dir/firmware.ota.bin" "" >/dev/null
# qm guest exec forwards at most 1 MiB of stdin: send 700 KB chunks.
tmp=$(mktemp -d); split -b 700000 "$fw" "$tmp/part."
for part in "$tmp"/part.*; do
  base64 <"$part" | ssh -o BatchMode=yes "$PVE" \
    "qm guest exec $VMID --timeout 60 --pass-stdin 1 -- sh -c 'base64 -d >> $WWW/$dir/firmware.ota.bin'" >/dev/null
done
rm -rf "$tmp"
remote_md5=$(guest "md5sum $WWW/$dir/firmware.ota.bin" "" | cut -d' ' -f1)
[ "$remote_md5" = "$md5" ] || { echo "upload corrupted: $remote_md5 != $md5" >&2; exit 1; }

url="${HA_PUBLIC_URL%/}/local/victor-ota/$dir/firmware.ota.bin"
code=$(curl -s -o /dev/null -w '%{http_code}' -r 0-0 "$url")
[ "$code" = "206" ] || [ "$code" = "200" ] || { echo "image not reachable from the internet: HTTP $code for $url" >&2; exit 1; }

pub() {  # topic payload
  guest "docker exec app_core_mosquitto mosquitto_pub -h localhost -u $MQTT_USER -P $MQTT_PASS -t $1 -m $2" "" >/dev/null
}
pub victor/node/text/ota_url/command "$url"
pub victor/node/text/ota_md5/command "$md5"
sleep 5
pub victor/node/button/flash_firmware_from_url/command PRESS

echo "update started; the node reboots in ~1-2 min. Watch it with:"
echo "  tools/mqtt-sub.sh 'victor/node/status' 180"
echo "then run: tools/ota-remote.sh --cleanup"
