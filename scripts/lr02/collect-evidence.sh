#!/bin/bash
# StudentLedger LR2 - collect factual evidence from inside a guest VM.
#
# Usage inside the guest:
#   bash collect-evidence.sh <SELF_IP> [<PEER_IP_1> <PEER_IP_2>]
#
# Writes a single report to stdout. The report is assembled from real command
# output only; nothing is asserted that was not executed on this machine.

set -u
SELF_IP="${1:-}"
shift || true
PEERS=("$@")

echo "===== StudentLedger LR2 evidence ====="
echo "collected: $(date -Is)"
echo "hostname: $(hostname)"

echo
echo "----- OS and architecture -----"
hostnamectl | sed -n '1,8p'
grep PRETTY_NAME /etc/os-release
uname -r
uname -m

echo
echo "----- required tools (LR2 item 5) -----"
git --version
python3 --version
python3 -m venv /tmp/lr2-venv-check >/dev/null 2>&1 && /tmp/lr2-venv-check/bin/python --version
rm -rf /tmp/lr2-venv-check

echo
echo "----- minimal GUI -----"
dpkg -l xubuntu-desktop-minimal lightdm 2>/dev/null | awk '/^ii/ {print $2, $3}'
systemctl is-enabled lightdm 2>/dev/null || true
pgrep -af 'lightdm$|Xorg|xfce4-session' | head -5 || echo "graphical session not running yet"

echo
echo "----- memory in use -----"
free -m | sed -n '1,2p'

echo
echo "----- network interfaces -----"
ip -br link
ip -br -4 address
ip route

echo
echo "----- static address of the internal segment -----"
# The netplan file is mode 600 root-owned; read it with sudo -n (passwordless).
sudo -n cat /etc/netplan/60-studentledger.yaml 2>/dev/null || echo "netplan file not readable"

if [ -n "$SELF_IP" ]; then
  echo
  echo "----- application on $SELF_IP -----"
  systemctl is-enabled studentledger.service 2>/dev/null || true
  systemctl is-active studentledger.service 2>/dev/null || true
  pgrep -af 'uvicorn app.main:app' | head -3 || echo "uvicorn process not found"
  curl -sS -i --max-time 5 "http://${SELF_IP}:8000/health" || echo "health request failed"
fi

echo
echo "----- project clone -----"
if [ -d /home/student/StudentLedger/.git ]; then
  sudo -u student git -C /home/student/StudentLedger remote -v
  sudo -u student git -C /home/student/StudentLedger branch --show-current
  sudo -u student git -C /home/student/StudentLedger rev-parse HEAD
  sudo -u student git -C /home/student/StudentLedger log --oneline -1
  /home/student/StudentLedger/.venv/bin/python --version
  sudo -u student /home/student/StudentLedger/.venv/bin/python -m pip check
else
  echo "project directory not found"
fi

echo
echo "----- ping all-to-all (LR2 item 4) -----"
for p in "${PEERS[@]}"; do
  echo "--- $SELF_IP -> $p"
  ping -c 4 -W 2 "$p" | tail -3
done

echo
echo "===== end of evidence ====="
