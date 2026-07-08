#!/usr/bin/env bash
# vasca_install.sh — Install VASCA binary and systemd service on Linux
# Source: SeCuardian 자체 개발 | License: Apache-2.0
# Usage: sudo ./deploy/scripts/vasca_install.sh
set -euo pipefail

BINARY_SRC="${BINARY_SRC:-VASCA/bin/vasca}"
BINARY_DST="/usr/local/bin/vasca"
SERVICE_SRC="deploy/systemd/vasca.service"
ENV_EXAMPLE="deploy/systemd/vasca.env.example"
ENV_DST="/etc/vasca/vasca.env"
DB_DIR="/var/lib/vasca"
SERVICE_USER="vasca"

if [[ $EUID -ne 0 ]]; then
  echo "ERROR: run as root (sudo $0)" >&2
  exit 1
fi

# 1. Build binary if not present
if [[ ! -f "$BINARY_SRC" ]]; then
  echo "Building VASCA binary..."
  (cd VASCA && CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -o bin/vasca ./cmd/vasca)
fi

# 2. Install binary
install -m 0755 "$BINARY_SRC" "$BINARY_DST"
echo "Installed: $BINARY_DST"

# 3. Create vasca system user
if ! id -u "$SERVICE_USER" &>/dev/null; then
  useradd --system --no-create-home --shell /usr/sbin/nologin "$SERVICE_USER"
  echo "Created system user: $SERVICE_USER"
fi

# 4. Create data directory
install -d -m 0750 -o "$SERVICE_USER" -g "$SERVICE_USER" "$DB_DIR"
echo "Data directory: $DB_DIR"

# 5. Install env file (skip if exists)
mkdir -p /etc/vasca
if [[ ! -f "$ENV_DST" ]]; then
  install -m 0640 -o root -g "$SERVICE_USER" "$ENV_EXAMPLE" "$ENV_DST"
  echo "Created env file: $ENV_DST (edit SECUARDIAN_TOKEN before starting)"
else
  echo "Env file exists, skipping: $ENV_DST"
fi

# 6. Install systemd service
install -m 0644 "$SERVICE_SRC" /etc/systemd/system/vasca.service
systemctl daemon-reload
echo "Installed systemd unit: vasca.service"

echo ""
echo "Next steps:"
echo "  1. Edit $ENV_DST — set SECUARDIAN_TOKEN and optionally SLACK_WEBHOOK_URL"
echo "  2. sudo systemctl enable --now vasca"
echo "  3. sudo systemctl status vasca"
