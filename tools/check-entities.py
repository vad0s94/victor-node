#!/usr/bin/env python3
"""Check that every Home Assistant entity id referenced by the dashboard and the
HA package exists in a firmware config (entity ids are predicted from ESPHome
names: <domain>.victor_<sanitized name>, discovery_object_id_generator: device_name).

  .venv/bin/python tools/check-entities.py [victor.yaml]
Exit code 1 if something is missing.
"""
import re
import subprocess
import sys
from pathlib import Path

import yaml

import shutil

ROOT = Path(__file__).resolve().parent.parent
cfg_file = sys.argv[1] if len(sys.argv) > 1 else "victor.yaml"
jk_src = ROOT / "tools/ref/jk-src/components"

esphome_bin = str(ROOT / ".venv/bin/esphome") if (ROOT / ".venv/bin/esphome").is_file() else shutil.which("esphome") or "esphome"
cmd = [esphome_bin]
if jk_src.is_dir():
    cmd += ["-s", "jk_bms_source", "../tools/ref/jk-src/components"]
cmd += ["config", cfg_file]
out = subprocess.run(cmd, cwd=ROOT / "esphome", capture_output=True, text=True)
if out.returncode != 0:
    sys.exit(out.stdout[-3000:] + out.stderr[-3000:])


class Loader(yaml.SafeLoader):
    pass


def _any_tag(loader, _suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)


Loader.add_multi_constructor("!", _any_tag)
text = out.stdout[out.stdout.index("esphome:"):]
config = yaml.load(text, Loader=Loader)

domains = {"sensor": "sensor", "text_sensor": "sensor", "binary_sensor": "binary_sensor",
           "switch": "switch", "select": "select", "number": "number", "button": "button", "text": "text"}
ids = set()


def walk(domain, node):
    if isinstance(node, dict):
        name = node.get("name")
        if isinstance(name, str) and not node.get("internal"):
            ids.add(f"{domains[domain]}.victor_{re.sub(r'[^a-z0-9_]', '_', name.lower().replace(' ', '_'))}")
        for key, value in node.items():
            if key != "name":
                walk(domain, value)
    elif isinstance(node, list):
        for item in node:
            walk(domain, item)


for domain in domains:
    walk(domain, config.get(domain, []))

refs = set()
for f in ("homeassistant/dashboards/dacha.yaml", "homeassistant/packages/victor.yaml"):
    refs |= set(re.findall(r"\b(?:sensor|binary_sensor|switch|select|number|button|text)\.victor_[a-z0-9_]+",
                           (ROOT / f).read_text()))

missing = sorted(r for r in refs if r not in ids)
print(f"{cfg_file}: {len(ids)} entities, {len(refs)} referenced, missing: {missing or 'none'}")
sys.exit(1 if missing else 0)
