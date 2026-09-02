#!/usr/bin/env bash
# ==============================================================================
# Proxmox VE LXC Automated Deployment Script (Debian / Ubuntu LXC)
# ==============================================================================
set -euo pipefail

echo "=== Desplegando Room Speaker Calibration en Proxmox LXC ==="

# Update packages and install python + alsa
apt-get update
apt-get install -y --no-install-recommends     python3     python3-pip     python3-venv     alsa-utils     git     curl

# Create target directory
INSTALL_DIR="/opt/room-speaker-calibration"
mkdir -p "$INSTALL_DIR"

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Actualizando repositorio existente..."
    git -C "$INSTALL_DIR" pull origin master
else
    echo "Clonando repositorio..."
    git clone https://github.com/sergiomh499/room-speaker-calibration.git "$INSTALL_DIR"
fi

# Create virtual environment
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# Create systemd service
cat << 'EOF' > /etc/systemd/system/yamaha-calibration-bridge.service
[Unit]
Description=Yamaha Room Speaker Calibration Bridge for Home Assistant
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/room-speaker-calibration
ExecStart=/opt/room-speaker-calibration/venv/bin/python3 /opt/room-speaker-calibration/scripts/ha_bridge.py --serve
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now yamaha-calibration-bridge

echo "=== Despliegue en Proxmox LXC completado exitosamente ==="
echo "Estado del servicio:"
systemctl status yamaha-calibration-bridge --no-pager
