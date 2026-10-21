#!/bin/bash
# Start LAN Web Chat and expose it securely via Cloudflare Tunnel

# Determine script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

# Check if chat server is already running on port 8000
python3 -c "import socket; s = socket.socket(); exit(0 if s.connect_ex(('127.0.0.1', 8000)) == 0 else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Starting Web Chat server in background..."
    python3 "$SCRIPT_DIR/web_chat.py" > /dev/null 2>&1 &
    sleep 1
fi

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "[WARNING] 'cloudflared' command not found!"
    echo "To install Cloudflare Tunnel on Linux:"
    echo "  curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb"
    echo "  sudo dpkg -i cloudflared.deb"
    echo ""
    echo "The local Web Chat is running at: http://localhost:8000"
    exit 1
fi

echo "Starting Cloudflare Tunnel to port 8000..."
cloudflared tunnel --url http://localhost:8000
