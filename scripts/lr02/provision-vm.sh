#!/bin/bash
# StudentLedger LR2 — подготовка стенда после установки ОС.
# Запуск внутри ВМ:  sudo bash provision-vm.sh <hostname> <netplan-файл> [внутренний-IP]
# Пример:            sudo bash provision-vm.sh studentledger-test netplan-192.168.56.11-test.yaml 192.168.56.11
#
# Скрипт: задаёт hostname, ставит минимальный GUI (Xubuntu minimal),
# ставит инструменты пункта 5 методички, настраивает статический адрес
# внутреннего сегмента, клонирует проект, готовит venv и включает
# автозапуск приложения службой systemd.
# Идемпотентен: повторный запуск не ломает уже настроенную систему.

set -u
HOSTNAME_NEW="${1:-}"
NETPLAN_SRC="${2:-}"
APP_IP="${3:-}"
REPO_URL="${REPO_URL:-https://github.com/PervuhinRoman/SLCA.git}"
PROJECT_DIR="/home/student/StudentLedger"
LOG="/home/student/provision.log"
MARK="### LR2-PROVISION-V1 ###"

if [ -z "$HOSTNAME_NEW" ]; then
  echo "usage: $0 <hostname> [netplan-file]" >&2
  exit 2
fi

{
  echo "$MARK start $(date -Is) hostname=$HOSTNAME_NEW"
  echo "=== whoami/os ==="
  id
  cat /etc/os-release | head -3
  uname -m

  echo "=== hostname ==="
  hostnamectl set-hostname "$HOSTNAME_NEW"
  hostnamectl

  echo "=== apt update ==="
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y

  echo "=== инструменты ЛР2 ==="
  apt-get install -y git python3 python3-venv python3-pip curl iputils-ping ca-certificates

  echo "=== минимальный GUI (Xubuntu minimal, XFCE + LightDM) ==="
  if dpkg -s xubuntu-desktop-minimal >/dev/null 2>&1; then
    echo "xubuntu-desktop-minimal уже установлен"
  else
    apt-get install -y --no-install-recommends xubuntu-desktop-minimal
  fi

  echo "=== сеть внутреннего сегмента ==="
  ip -br link
  ip -br -4 address
  ip route
  if [ -n "$NETPLAN_SRC" ] && [ -f "$NETPLAN_SRC" ]; then
    install -m 600 "$NETPLAN_SRC" /etc/netplan/60-studentledger.yaml
    netplan generate
    netplan apply
    ip -br -4 address
    ip route
  else
    echo "netplan-файл не передан: сеть не изменялась"
  fi

  echo "=== версии инструментов ==="
  git --version
  python3 --version
  python3 -m venv /tmp/studentledger-venv-check
  /tmp/studentledger-venv-check/bin/python --version
  rm -rf /tmp/studentledger-venv-check

  if [ -n "$REPO_URL" ]; then
    echo "=== клон репозитория ==="
    if [ -d "$PROJECT_DIR/.git" ]; then
      sudo -u student git -C "$PROJECT_DIR" fetch --all --prune
      sudo -u student git -C "$PROJECT_DIR" status --short --branch
    else
      rm -rf "$PROJECT_DIR"
      sudo -u student git clone --branch master "$REPO_URL" "$PROJECT_DIR"
    fi
    sudo -u student git -C "$PROJECT_DIR" branch --show-current
    sudo -u student git -C "$PROJECT_DIR" rev-parse HEAD

    echo "=== venv и зависимости ==="
    if [ ! -x "$PROJECT_DIR/.venv/bin/python" ]; then
      sudo -u student python3 -m venv "$PROJECT_DIR/.venv"
    fi
    sudo -u student "$PROJECT_DIR/.venv/bin/python" -m pip install -r "$PROJECT_DIR/requirements.txt"
    sudo -u student "$PROJECT_DIR/.venv/bin/python" -m pip check

    # Адрес прослушивания: третий аргумент, иначе берётся из переданного Netplan.
    if [ -z "$APP_IP" ] && [ -f /etc/netplan/60-studentledger.yaml ]; then
      APP_IP=$(grep -m1 -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' /etc/netplan/60-studentledger.yaml)
    fi
    if [ -z "$APP_IP" ]; then
      APP_IP="127.0.0.1"
      echo "внимание: адрес прослушивания не задан, используется $APP_IP"
    fi

    echo "=== автозапуск приложения службой systemd (адрес $APP_IP) ==="
    cat > /etc/systemd/system/studentledger.service <<UNIT
[Unit]
Description=StudentLedger FastAPI prototype (LR2)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=student
Group=student
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/.venv/bin/python -m uvicorn app.main:app --host $APP_IP --port 8000
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT
    systemctl daemon-reload
    systemctl enable --now studentledger.service
    sleep 5
    systemctl is-enabled studentledger.service
    systemctl is-active studentledger.service
    curl -sS -i --max-time 5 "http://${APP_IP}:8000/health" || echo "проверка /health не прошла"
  fi

  echo "$MARK done $(date -Is)"
} >"$LOG" 2>&1

chown student:student "$LOG" 2>/dev/null || true
chmod 644 "$LOG" 2>/dev/null || true
echo "готово: см. $LOG"
cat "$LOG"
