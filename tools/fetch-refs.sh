#!/usr/bin/env bash
# One-time setup for a fresh checkout (tools/ref/ and .venv/ are git-ignored):
#   - Python venv with the pinned ESPHome version
#   - syssi/esphome-jk-bms at the pinned commit as a tarball (git clone of that
#     repo is ~100 MB and very slow from this network; codeload is fast)
#   - upstream reference copies used to build the vendored files
set -euo pipefail
cd "$(dirname "$0")/.."

ESPHOME_VERSION=2026.9.1
JK_COMMIT=59c994e726c34b123e43eb0090736fd94706f0db
AVER_COMMIT=9c607d6d2f61288da019f046ca12c09b39190b05
TRAVIS_COMMIT=2c7f942b7e306367d916b8b0c2a913222de9973d

if [ ! -x .venv/bin/esphome ]; then
  uv venv -q --python 3.12 .venv
  uv pip install -q --python .venv "esphome==${ESPHOME_VERSION}"
fi
.venv/bin/esphome version

mkdir -p tools/ref/jk-src tools/ref/aver tools/ref/travis
if [ ! -d tools/ref/jk-src/components/jk_bms_ble ]; then
  curl -sSL "https://codeload.github.com/syssi/esphome-jk-bms/tar.gz/${JK_COMMIT}" \
    | tar -xz -C tools/ref/jk-src --strip-components=1
fi

raw() { curl -sSL -o "$2" "https://raw.githubusercontent.com/$1"; }
for f in src/powmr-inverter/modules/inverter.yaml src/powmr-inverter/modules/inverter-info.yaml \
         src/powmr-inverter/modules/pow-hvm6.2m-48v.yaml src/powmr-inverter/modules/common-sensors.yaml \
         docs/registers-map.md examples/lovelace-powmr.yaml; do
  mkdir -p "tools/ref/aver/$(dirname "$f")"
  raw "aver-ua/esphome-hybrid-inverter-2341/${AVER_COMMIT}/$f" "tools/ref/aver/$f"
done
raw "Travis90x/esphome-pipsolar/${TRAVIS_COMMIT}/diagnostics/ESP32_ESP8266_test_protocol_solar_inverter_RS232.yaml" \
    tools/ref/travis/test_protocol.yaml

echo "ready: JK_BMS_SOURCE=../tools/ref/jk-src/components tools/build.sh victor.yaml"
