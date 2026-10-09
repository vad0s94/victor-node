#!/usr/bin/env bash
# Node logs forwarded over MQTT (level set by mqtt_log_level; INFO in victor-probe.yaml).
#   tools/mqtt-log.sh [seconds]
exec "$(dirname "$0")/mqtt-sub.sh" 'victor/node/debug' "${1:-180}"
