#!/bin/bash
# LR3: install Docker Engine and Compose plugin on Ubuntu 24.04.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "Запустите с sudo: sudo bash install-docker.sh" >&2
    exit 1
fi

export DEBIAN_FRONTEND=noninteractive

# The Ubuntu live installer may leave a file:/cdrom source that breaks apt.
grep -rls 'file:/cdrom' /etc/apt/sources.list /etc/apt/sources.list.d 2>/dev/null | xargs -r rm -f || true
sed -i '\#file:///cdrom#d' /etc/apt/sources.list || true

apt-get update -y
apt-get install -y ca-certificates curl

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
    > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

usermod -aG docker student

docker --version
docker compose version
