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
../.venv/bin/esphome "${args[@]}" compile "$cfg"

ota=$(find .esphome/build/victor -name firmware.ota.bin -newer "$cfg" -print -quit)
factory=$(find .esphome/build/victor -name firmware.factory.bin -newer "$cfg" -print -quit)
[ -n "$ota" ] || { echo "build output not found under .esphome/build/victor" >&2; exit 1; }

mkdir -p build
cp "$ota" "build/${name}.ota.bin"
[ -n "$factory" ] && cp "$factory" "build/${name}.factory.bin"
md5 -q "build/${name}.ota.bin" > "build/${name}.ota.md5"
ls -l build/"${name}".*
