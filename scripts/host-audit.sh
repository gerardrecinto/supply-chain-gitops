#!/usr/bin/env bash
# Quick Linux build-host check: pending security updates, world-writable dirs in PATH, ssh root login.
set -u
fail=0
note() { echo "FAIL $1"; fail=1; }

if command -v apt-get >/dev/null 2>&1; then
  n=$(apt-get -s upgrade 2>/dev/null | grep -c '^Inst.*security' || true)
  [ "$n" -eq 0 ] || note "$n pending security updates"
elif command -v dnf >/dev/null 2>&1; then
  dnf -q updateinfo list --security 2>/dev/null | grep -q . && note "pending security updates"
fi

IFS=: read -ra dirs <<<"$PATH"
for d in "${dirs[@]}"; do
  [ -d "$d" ] && [ -n "$(find "$d" -maxdepth 0 -perm -0002 2>/dev/null)" ] && note "PATH dir $d is world-writable"
done

grep -Eqi '^\s*PermitRootLogin\s+yes' /etc/ssh/sshd_config 2>/dev/null && note "ssh root login enabled"
[ "$fail" -eq 0 ] && echo "ok"
exit "$fail"
