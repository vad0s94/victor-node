#!/usr/bin/env bash
# Compile a node firmware and copy the images to esphome/build/.
#   tools/build.sh victor.yaml        -> build/victor.factory.bin, build/victor.ota.bin, build/victor.ota.md5
# Slow git to GitHub? Use an unpacked syssi/esphome-jk-bms tarball of the pinned commit:
#   JK_BMS_SOURCE=../tools/ref/jk-src/components tools/build.sh victor.yaml
# First flash over USB:  .venv/bin/esphome run esphome/<file> --device /dev/cu.usbserial-*
set -euo pipefail

cd "$(dirname "$0")/../esphome"
cfg="${1:?usage: tools/build.sh <config.yaml>}"
name="${cfg%.yaml}"

[ -f secrets.yaml ] || { echo "esphome/secrets.yaml missing: copy secrets.example.yaml and fill it in" >&2; exit 1; }

args=()
[ -n "${JK_BMS_SOURCE:-}" ] && args+=(-s jk_bms_source "$JK_BMS_SOURCE")
[ -n "${DALY_BMS_SOURCE:-}" ] && args+=(-s daly_bms_source "$DALY_BMS_SOURCE")
[ -n "${JBD_BMS_SOURCE:-}" ] && args+=(-s jbd_bms_source "$JBD_BMS_SOURCE")

ESPHOME_BIN="../.venv/bin/esphome"
[ -x "$ESPHOME_BIN" ] || ESPHOME_BIN="esphome"

"$ESPHOME_BIN" "${args[@]}" compile "$cfg"

ota=$(find .esphome/build -name firmware.ota.bin -newer "$cfg" -print -quit)
factory=$(find .esphome/build -name firmware.factory.bin -newer "$cfg" -print -quit)
[ -n "$ota" ] || { echo "build output not found under .esphome/build" >&2; exit 1; }

mkdir -p build
cp "$ota" "build/${name}.ota.bin"
[ -n "$factory" ] && cp "$factory" "build/${name}.factory.bin"

if command -v md5 >/dev/null 2>&1; then
  md5 -q "build/${name}.ota.bin" > "build/${name}.ota.md5"
elif command -v md5sum >/dev/null 2>&1; then
  md5sum "build/${name}.ota.bin" | awk '{print $1}' > "build/${name}.ota.md5"
fi

ls -l build/"${name}".*
