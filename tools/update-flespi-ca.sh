#!/usr/bin/env bash
# Rebuild esphome/certs/flespi-ca.pem and the CA block in packages/mqtt-flespi.yaml
# from the roots in the macOS system keychain that validate mqtt.flespi.io:8883.
set -euo pipefail
cd "$(dirname "$0")/.."

security find-certificate -a -p /System/Library/Keychains/SystemRootCertificates.keychain > /tmp/macos-roots.pem
echo | openssl s_client -connect mqtt.flespi.io:8883 -servername mqtt.flespi.io -showcerts 2>/dev/null > /tmp/flespi-chain.txt

python3 - <<'PY'
import re, subprocess
chain = open('/tmp/flespi-chain.txt').read()
issuers = set(re.findall(r'^\s*i:(.*)$', chain, re.M))
roots = re.findall(r'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----', open('/tmp/macos-roots.pem').read(), re.S)
keep = []
for pem in roots:
    subj = subprocess.run(['openssl', 'x509', '-noout', '-subject'],
                          input=pem, capture_output=True, text=True).stdout.strip().removeprefix('subject=')
    if any(subj.replace(' ', '') == i.replace(' ', '') for i in issuers):
        keep.append(pem)
if not keep:
    raise SystemExit('no matching root found in the macOS keychain')
open('esphome/certs/flespi-ca.pem', 'w').write('\n'.join(keep) + '\n')
pkg = 'esphome/packages/mqtt-flespi.yaml'
s = open(pkg).read()
head = s[:s.index('  certificate_authority: |')]
block = '\n'.join('      ' + l for l in '\n'.join(keep).splitlines())
open(pkg, 'w').write(head + '  certificate_authority: |\n' + block + '\n')
print(f'{len(keep)} root(s) written')
PY

echo | openssl s_client -connect mqtt.flespi.io:8883 -servername mqtt.flespi.io -CAfile esphome/certs/flespi-ca.pem 2>/dev/null | grep "Verify return code"
