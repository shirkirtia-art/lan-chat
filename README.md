# 💬 LAN Chat & File Sharing System

<p align="center">
  <b>A lightweight, zero-dependency local network chat & file-sharing server with a modern Web UI and classic CLI terminal mode.</b>
  <br />
  <i>Chat with phones, tablets, and PCs on the same Wi-Fi — or securely over the internet via Cloudflare Tunnel.</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg?style=flat-square&logo=python&logoColor=white" alt="Python 3.8+" />
  <img src="https://img.shields.io/badge/dependencies-0%20(Pure%20StdLib)-success.svg?style=flat-square" alt="Zero Dependencies" />
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Android%20%7C%20iOS-orange.svg?style=flat-square" alt="Cross-Platform" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg?style=flat-square" alt="License" />
</p>

---

## ✨ Features

- ⚡ **100% Pure Python — Zero Dependencies**: No `pip install`, no virtual environments, no node.js. Runs out of the box with standard Python 3.
- 📱 **Modern Web Interface**: Responsive dark-mode UI designed for smartphones (iOS/Android), tablets, and desktop browsers.
- 📎 **Rich Media & File Attachments**:
  - **Drag & Drop**: Drop files directly into the browser chat window.
  - **Clipboard Paste**: Press `Ctrl+V` (or `Cmd+V`) to instantly share screenshots.
  - **Inline Media Previews**: View image thumbnails, stream audio files, and watch videos directly in the chat feed.
  - **Direct Downloads**: Share documents, PDFs, ZIP archives, and source code files up to 50MB.
- 👥 **Real-Time Presence & Nicknames**: Active online user counter, custom nicknames, typing feedback, and auto-scrolling chat history.
- 🌐 **Instant Cloudflare Tunnel**: One-click launchers for **Windows (`.bat`)** and **Linux/macOS (`.sh`)** to expose your server over encrypted HTTPS without configuring router port-forwarding or dynamic DNS.
- 💻 **Classic CLI Mode**: Fast, multi-threaded raw socket server and terminal client for command-line enthusiasts.
- 🔒 **Private & Local-First**: Messages and files stay entirely on your local network (or inside your private tunnel). No telemetry, tracking, or cloud databases.

---

## 🏗️ Architecture

```text
               ┌────────────────────────────────────────────────────────┐
               │           Host Machine (Windows / Mac / Linux)         │
               │   Runs: python3 web_chat.py (Port 8000)                │
               │   Storage: uploads/ (Attachments)                      │
               └───────────────▲────────────────────────▲───────────────┘
                               │                        │
             Local Wi-Fi / LAN │                        │ Cloudflare Tunnel
      (http://192.168.x.x:8000)│                        │ (https://*.trycloudflare.com)
                               ▼                        ▼
               ┌────────────────────────┐      ┌────────────────────────┐
               │   Local Wi-Fi Devices  │      │ Remote Internet Users  │
               │  • iPhone / iPad       │      │  • Remote Coworkers    │
               │  • Android Phones      │      │  • Off-site Laptops    │
               │  • Laptops / Desktops  │      │  • Any Web Browser     │
               └────────────────────────┘      └────────────────────────┘
```

---

## 🚀 Quick Start

### Option 1: Web Browser Chat (Recommended)

No client installation required. Any device with a modern web browser can connect.

#### 1. Start the Server on the Host Machine

- **Windows**: Double-click [`start_web_chat.bat`](file:///home/ciphyrtech/Downloads/lan-chat/start_web_chat.bat) or run:
  ```cmd
  python web_chat.py
  ```
- **Linux / macOS**: Run:
  ```bash
  python3 web_chat.py
  ```

The server displays your local IP and URL:
```text
=================================================================
 LAN WEB CHAT & FILE SHARING RUNNING
=================================================================
 Local Wi-Fi URL:  http://192.168.1.5:8000
 Uploads folder:   /path/to/lan-chat/uploads
 Attachments:      Images, Videos, Audio, PDFs, ZIP, Code, etc.
=================================================================
```

#### 2. Connect from Any Device
Open the displayed URL (e.g. `http://192.168.1.5:8000`) on any smartphone, tablet, or PC connected to the same Wi-Fi network. Choose a nickname and start chatting!

---

### Option 2: Secure Public Access via Cloudflare Tunnel

Need to chat with someone outside your Wi-Fi network? Use the automated Cloudflare Tunnel launcher to generate a temporary, encrypted HTTPS link with **zero port-forwarding**.

> **Prerequisite**: Install `cloudflared`:
> - **Windows**: `winget install Cloudflare.cloudflared`
> - **macOS**: `brew install cloudflared`
> - **Linux**: `sudo apt install cloudflared` (or grab the `.deb` / `.rpm` from Cloudflare)

#### Launchers:

- **Windows**: Double-click [`start_cloudflare.bat`](file:///home/ciphyrtech/Downloads/lan-chat/start_cloudflare.bat) (or run in CMD / PowerShell):
  ```cmd
  start_cloudflare.bat
  ```
- **Linux / macOS**: Run:
  ```bash
  chmod +x start_cloudflare.sh
  ./start_cloudflare.sh
  ```

The launcher will:
1. Verify if the web chat server is running on port 8000 (and starts it automatically if it isn't).
2. Establish a secure Cloudflare Tunnel.
3. Print a public `https://<unique-subdomain>.trycloudflare.com` URL to share with remote users.

---

### Option 3: Terminal Socket Chat (Classic CLI)

Ideal for command-line pair programming and lightweight text communication.

#### Step 1: Start the Server (Host)
```bash
python3 server.py
# Windows: python server.py
```
*Outputs listening port `5555` and local IP.*

#### Step 2: Connect Clients
On any machine on the same network:
```bash
python3 client.py
# Windows: python client.py
```
- Enter the Host's IP address (e.g., `192.168.1.5`).
- Enter your nickname.
- Send messages in real-time (type `/quit` to leave).

---

## 📎 File Sharing Capabilities

| Feature | Method | Supported Types |
| :--- | :--- | :--- |
| **File Browser** | Click the 📎 button | Photos, Videos, Audio, Documents, Archives, Code |
| **Drag & Drop** | Drag any file into the browser window | Any file format up to 50MB |
| **Clipboard Paste** | `Ctrl+V` (Windows/Linux) or `Cmd+V` (macOS) | Direct screenshot paste (PNG/JPEG) |
| **Media Player** | Inline player inside chat feed | MP4, WebM, MP3, WAV, OGG |
| **Image Lightbox** | Click thumbnail to view full-size | PNG, JPG, GIF, WebP, SVG |
| **Download Card** | Single-click download button | PDF, ZIP, TAR, TXT, PY, JS, DOCX, etc. |

---

## 🔍 How to Find Your Host IP Manually

If you need to look up your host IP manually:

| OS | Command | Look For |
| :--- | :--- | :--- |
| **Windows** | `ipconfig` in Command Prompt | `IPv4 Address` (e.g., `192.168.1.x`) |
| **macOS** | `ipconfig getifaddr en0` | Wi-Fi IP address |
| **Linux** | `hostname -I` or `ip a` | First private address (`192.168.x.x` or `10.x.x.x`) |
| **Android / iOS** | Wi-Fi Settings &rarr; Network Details | `IP address` |

---

## 📁 Project Structure

```text
lan-chat/
├── client.py              # Command-line socket client
├── server.py              # Command-line socket server (port 5555)
├── web_chat.py            # Zero-dependency HTTP & WebSocket-like Web Chat (port 8000)
├── start_cloudflare.bat   # Windows 1-click launcher for Web Chat + Cloudflare Tunnel
├── start_cloudflare.sh    # Linux/macOS 1-click launcher for Web Chat + Cloudflare Tunnel
├── start_web_chat.bat     # Windows 1-click launcher for local Web Chat
├── uploads/               # Directory where shared files and attachments are stored
├── .gitignore             # Git ignore rules for cached files and chat uploads
└── README.md              # Project documentation
```

---

## 🛡️ Firewall & Network Troubleshooting

1. **Both devices must be on the same network**:
   - Verify that your phone or client is connected to the same Wi-Fi router, not mobile data (4G/5G).
   - Ensure your router does not have **"AP Isolation" / "Client Isolation"** turned on (common on public or guest Wi-Fi networks).
2. **Firewall Prompts**:
   - **Windows**: When prompted by Windows Defender Firewall, click **Allow access** for Private networks.
   - **Linux (`ufw`)**: If ports are blocked, run:
     ```bash
     sudo ufw allow 8000/tcp comment "LAN Web Chat"
     sudo ufw allow 5555/tcp comment "LAN CLI Chat"
     ```
3. **Port 8000 Already in Use**:
   - You can change `PORT = 8000` at the top of [`web_chat.py`](file:///home/ciphyrtech/Downloads/lan-chat/web_chat.py#L21) to any open port (e.g., `8080`, `9000`).

---

## 📄 License

This project is open-source and released under the [MIT License](https://opensource.org/licenses/MIT). Free to use, modify, and distribute.
