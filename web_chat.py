#!/usr/bin/env python3
"""
Zero-Dependency Web-based LAN Chat Server with File Attachment & Sharing Support
Allows anyone on the local network or Cloudflare Tunnel to chat and share files from ANY device.
Uses pure Python standard library (no pip install needed).
"""

import http.server
import json
import mimetypes
import os
import re
import socket
import sys
import threading
import time
import urllib.parse
from datetime import datetime
from urllib.parse import urlparse, parse_qs

PORT = 8000
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Chat state (thread-safe)
lock = threading.Lock()
messages = []  # list of {"id": int, "user": str, "text": str, "time": str, "system": bool, "file": dict|None}
active_users = {}  # username -> last_seen_timestamp (epoch)
message_id_counter = 0

def get_local_ip():
    """Detect the machine's local LAN IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def format_size(num_bytes):
    """Format file size into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}" if unit != 'B' else f"{int(num_bytes)} B"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>LAN Chat & File Sharing</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: #0f172a;
    color: #e2e8f0;
    display: flex;
    flex-direction: column;
    height: 100vh;
    height: 100dvh;
    overflow: hidden;
  }
  header {
    background: #1e293b;
    padding: 12px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #334155;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    z-index: 10;
  }
  .header-left { display: flex; align-items: center; gap: 10px; }
  .status-dot {
    width: 10px; height: 10px; border-radius: 50%; background: #10b981;
    box-shadow: 0 0 8px #10b981;
  }
  h1 { font-size: 1.1rem; font-weight: 600; color: #f8fafc; }
  .badge {
    background: #3b82f6;
    color: white;
    font-size: 0.75rem;
    padding: 2px 8px;
    border-radius: 999px;
    font-weight: 500;
  }
  .header-right {
    font-size: 0.85rem;
    color: #94a3b8;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .change-nick-btn {
    background: #334155;
    color: #f1f5f9;
    border: none;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    cursor: pointer;
    transition: background 0.15s;
  }
  .change-nick-btn:hover { background: #475569; }

  #messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    scroll-behavior: smooth;
  }
  .msg-wrapper {
    display: flex;
    flex-direction: column;
    max-width: 82%;
    animation: fadeIn 0.15s ease-out;
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .msg-incoming { align-self: flex-start; }
  .msg-outgoing { align-self: flex-end; }
  .msg-meta {
    font-size: 0.72rem;
    color: #64748b;
    margin-bottom: 4px;
    display: flex;
    gap: 6px;
  }
  .msg-outgoing .msg-meta { align-self: flex-end; }
  .msg-user { font-weight: 600; color: #38bdf8; }
  .msg-bubble {
    padding: 10px 14px;
    border-radius: 14px;
    line-height: 1.4;
    font-size: 0.95rem;
    word-break: break-word;
    white-space: pre-wrap;
  }
  .msg-incoming .msg-bubble {
    background: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
    border-bottom-left-radius: 3px;
  }
  .msg-outgoing .msg-bubble {
    background: #2563eb;
    color: #ffffff;
    border-bottom-right-radius: 3px;
  }
  .msg-system {
    align-self: center;
    font-size: 0.78rem;
    color: #94a3b8;
    background: rgba(30, 41, 59, 0.6);
    padding: 4px 14px;
    border-radius: 999px;
    border: 1px solid #334155;
    margin: 4px 0;
  }

  /* File attachment cards */
  .chat-file-img {
    max-width: 280px;
    max-height: 280px;
    border-radius: 10px;
    display: block;
    margin-bottom: 6px;
    cursor: pointer;
    object-fit: cover;
    transition: transform 0.15s;
    border: 1px solid rgba(255,255,255,0.1);
  }
  .chat-file-img:hover { transform: scale(1.02); }
  .chat-file-video {
    max-width: 280px;
    max-height: 240px;
    border-radius: 10px;
    display: block;
    margin-bottom: 6px;
    outline: none;
  }
  .chat-file-audio {
    width: 260px;
    margin-bottom: 6px;
    display: block;
  }
  .file-card {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(15, 23, 42, 0.6);
    padding: 8px 12px;
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 4px;
    max-width: 320px;
  }
  .file-icon { font-size: 1.6rem; line-height: 1; }
  .file-info {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  .file-name {
    font-size: 0.88rem;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: #f8fafc;
  }
  .file-size { font-size: 0.72rem; color: #94a3b8; }
  .file-download-btn {
    background: #3b82f6;
    color: white;
    text-decoration: none;
    font-size: 0.8rem;
    padding: 5px 10px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    gap: 4px;
    font-weight: 500;
    transition: background 0.15s;
  }
  .file-download-btn:hover { background: #2563eb; }

  /* Footer & Input bar */
  footer {
    background: #1e293b;
    border-top: 1px solid #334155;
    padding: 10px 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  /* File preview preview strip before sending */
  #attachment-preview {
    display: none;
    align-items: center;
    gap: 10px;
    background: #0f172a;
    border: 1px solid #3b82f6;
    border-radius: 8px;
    padding: 6px 12px;
    max-width: 900px;
    margin: 0 auto;
    width: 100%;
    animation: fadeIn 0.15s ease-out;
  }
  .preview-thumb {
    width: 36px; height: 36px;
    object-fit: cover;
    border-radius: 6px;
    background: #334155;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem;
  }
  .preview-info {
    flex: 1;
    overflow: hidden;
    font-size: 0.82rem;
  }
  .preview-name {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-weight: 500;
    color: #f1f5f9;
  }
  .preview-size { color: #64748b; font-size: 0.72rem; }
  .cancel-attach-btn {
    background: transparent;
    border: none;
    color: #ef4444;
    font-size: 1.1rem;
    cursor: pointer;
    padding: 4px 6px;
  }

  form {
    display: flex;
    align-items: center;
    gap: 8px;
    max-width: 900px;
    margin: 0 auto;
    width: 100%;
  }
  .attach-btn {
    background: #334155;
    border: 1px solid #475569;
    color: #f1f5f9;
    width: 44px;
    height: 44px;
    border-radius: 10px;
    font-size: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
    flex-shrink: 0;
  }
  .attach-btn:hover { background: #475569; border-color: #3b82f6; }
  #msg-input {
    flex: 1;
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.95rem;
    color: #f8fafc;
    outline: none;
    transition: border-color 0.2s;
    height: 44px;
  }
  #msg-input:focus { border-color: #3b82f6; }
  #send-btn {
    background: #2563eb;
    color: white;
    border: none;
    height: 44px;
    padding: 0 20px;
    border-radius: 10px;
    font-weight: 600;
    cursor: pointer;
    font-size: 0.95rem;
    transition: background 0.15s;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }
  #send-btn:hover { background: #1d4ed8; }
  #send-btn:disabled { background: #475569; cursor: not-allowed; }

  /* Drag and drop overlay */
  #drop-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.85);
    border: 3px dashed #3b82f6;
    z-index: 99;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 12px;
    color: #38bdf8;
    font-size: 1.2rem;
    font-weight: 600;
    pointer-events: none;
  }

  /* Nickname Modal */
  .modal-overlay {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.7);
    display: flex; align-items: center; justify-content: center;
    z-index: 100;
  }
  .modal {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 24px;
    width: 90%;
    max-width: 360px;
    text-align: center;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4);
  }
  .modal h2 { margin-bottom: 8px; color: #f8fafc; font-size: 1.25rem; }
  .modal p { font-size: 0.88rem; color: #94a3b8; margin-bottom: 16px; }
  .modal input {
    width: 100%;
    background: #0f172a;
    border: 1px solid #475569;
    border-radius: 8px;
    padding: 10px 14px;
    color: #f8fafc;
    font-size: 1rem;
    margin-bottom: 16px;
    outline: none;
  }
  .modal button {
    width: 100%;
    background: #2563eb;
    color: white;
    border: none;
    padding: 10px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
  }
</style>
</head>
<body>

<div id="drop-overlay">
  <div style="font-size: 3rem;">📁</div>
  <div>Drop file to attach & share</div>
</div>

<header>
  <div class="header-left">
    <div class="status-dot"></div>
    <h1>LAN Chat & Files</h1>
    <span class="badge" id="online-count">1 online</span>
  </div>
  <div class="header-right">
    <span id="display-nick">...</span>
    <button class="change-nick-btn" onclick="openNickModal()">Change</button>
  </div>
</header>

<div id="messages-container"></div>

<footer>
  <!-- Attachment Preview Strip -->
  <div id="attachment-preview">
    <div class="preview-thumb" id="preview-thumb">📄</div>
    <div class="preview-info">
      <div class="preview-name" id="preview-name">filename.ext</div>
      <div class="preview-size" id="preview-size">0 KB</div>
    </div>
    <button type="button" class="cancel-attach-btn" onclick="clearAttachment()" title="Remove file">✕</button>
  </div>

  <form id="chat-form" onsubmit="handleSend(event)">
    <input type="file" id="file-input" style="display: none;" onchange="handleFileSelected(event)" />
    <button type="button" class="attach-btn" onclick="document.getElementById('file-input').click()" title="Attach file or image">📎</button>
    <input type="text" id="msg-input" placeholder="Type a message, paste image, or drop file..." autocomplete="off" />
    <button type="submit" id="send-btn">Send</button>
  </form>
</footer>

<!-- Nickname Modal -->
<div class="modal-overlay" id="nick-modal" style="display: none;">
  <div class="modal">
    <h2>Choose Nickname</h2>
    <p>Enter your name so others in the chat know who you are.</p>
    <form onsubmit="saveNickname(event)">
      <input type="text" id="nick-input" placeholder="Your Name" maxlength="20" autofocus required />
      <button type="submit">Join Chat</button>
    </form>
  </div>
</div>

<script>
  let myNickname = localStorage.getItem('lan_chat_nickname') || '';
  let lastMessageId = 0;
  let selectedFile = null;

  const container = document.getElementById('messages-container');
  const input = document.getElementById('msg-input');
  const sendBtn = document.getElementById('send-btn');
  const fileInput = document.getElementById('file-input');
  const attachPreview = document.getElementById('attachment-preview');
  const previewThumb = document.getElementById('preview-thumb');
  const previewName = document.getElementById('preview-name');
  const previewSize = document.getElementById('preview-size');
  const dropOverlay = document.getElementById('drop-overlay');
  const nickModal = document.getElementById('nick-modal');
  const nickInput = document.getElementById('nick-input');
  const displayNick = document.getElementById('display-nick');
  const onlineCount = document.getElementById('online-count');

  function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function playNotificationSound() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.1);
      gain.gain.setValueAtTime(0.08, ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.001, ctx.currentTime + 0.2);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.2);
    } catch(e) {}
  }

  function setAttachment(file) {
    if (!file) return;
    if (file.size > 50 * 1024 * 1024) {
      alert("File is too large! Maximum allowed size is 50 MB.");
      return;
    }
    selectedFile = file;
    previewName.textContent = file.name;
    previewSize.textContent = formatBytes(file.size);

    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      previewThumb.innerHTML = `<img src="${url}" style="width:100%;height:100%;object-fit:cover;border-radius:4px;" />`;
    } else if (file.type.startsWith('video/')) {
      previewThumb.innerHTML = '🎬';
    } else if (file.type.startsWith('audio/')) {
      previewThumb.innerHTML = '🎵';
    } else {
      previewThumb.innerHTML = '📄';
    }

    attachPreview.style.display = 'flex';
    input.focus();
  }

  function clearAttachment() {
    selectedFile = null;
    fileInput.value = '';
    attachPreview.style.display = 'none';
    previewThumb.innerHTML = '📄';
  }

  function handleFileSelected(e) {
    if (e.target.files && e.target.files[0]) {
      setAttachment(e.target.files[0]);
    }
  }

  // Drag and drop handling
  let dragCounter = 0;
  window.addEventListener('dragenter', (e) => {
    e.preventDefault();
    dragCounter++;
    dropOverlay.style.display = 'flex';
  });
  window.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dragCounter--;
    if (dragCounter <= 0) {
      dropOverlay.style.display = 'none';
      dragCounter = 0;
    }
  });
  window.addEventListener('dragover', (e) => e.preventDefault());
  window.addEventListener('drop', (e) => {
    e.preventDefault();
    dragCounter = 0;
    dropOverlay.style.display = 'none';
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
      setAttachment(e.dataTransfer.files[0]);
    }
  });

  // Clipboard paste support (e.g. pasted screenshots)
  window.addEventListener('paste', (e) => {
    if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
      setAttachment(e.clipboardData.files[0]);
    }
  });

  function openNickModal() {
    nickInput.value = myNickname;
    nickModal.style.display = 'flex';
    setTimeout(() => nickInput.focus(), 50);
  }

  function saveNickname(e) {
    e.preventDefault();
    const val = nickInput.value.trim();
    if (!val) return;
    const oldNick = myNickname;
    myNickname = val;
    localStorage.setItem('lan_chat_nickname', myNickname);
    displayNick.textContent = myNickname;
    nickModal.style.display = 'none';
    input.focus();

    if (oldNick && oldNick !== myNickname) {
      sendMessageToServer(`* changed name from ${oldNick} to ${myNickname} *`, true);
    } else if (!oldNick) {
      sendMessageToServer(`* ${myNickname} entered the chat *`, true);
    }
  }

  function renderMessage(msg) {
    if (msg.system) {
      const div = document.createElement('div');
      div.className = 'msg-system';
      div.textContent = `[${msg.time}] ${msg.text}`;
      container.appendChild(div);
    } else {
      const isMe = msg.user === myNickname;
      const wrap = document.createElement('div');
      wrap.className = 'msg-wrapper ' + (isMe ? 'msg-outgoing' : 'msg-incoming');

      const meta = document.createElement('div');
      meta.className = 'msg-meta';
      if (!isMe) {
        const userSpan = document.createElement('span');
        userSpan.className = 'msg-user';
        userSpan.textContent = msg.user;
        meta.appendChild(userSpan);
      }
      const timeSpan = document.createElement('span');
      timeSpan.textContent = msg.time;
      meta.appendChild(timeSpan);
      wrap.appendChild(meta);

      const bubble = document.createElement('div');
      bubble.className = 'msg-bubble';

      // Render file if present
      if (msg.file) {
        const fileObj = msg.file;
        if (fileObj.type === 'image') {
          bubble.innerHTML += `<a href="${fileObj.url}" target="_blank" rel="noopener"><img src="${fileObj.url}" class="chat-file-img" alt="${escapeHtml(fileObj.name)}" /></a>`;
        } else if (fileObj.type === 'video') {
          bubble.innerHTML += `<video src="${fileObj.url}" controls class="chat-file-video"></video>`;
        } else if (fileObj.type === 'audio') {
          bubble.innerHTML += `<audio src="${fileObj.url}" controls class="chat-file-audio"></audio>`;
        } else {
          bubble.innerHTML += `
            <div class="file-card">
              <div class="file-icon">📄</div>
              <div class="file-info">
                <div class="file-name" title="${escapeHtml(fileObj.name)}">${escapeHtml(fileObj.name)}</div>
                <div class="file-size">${fileObj.size}</div>
              </div>
              <a href="${fileObj.url}" download="${escapeHtml(fileObj.name)}" class="file-download-btn">⬇️ Download</a>
            </div>
          `;
        }
      }

      if (msg.text) {
        const textSpan = document.createElement('span');
        textSpan.textContent = msg.text;
        bubble.appendChild(textSpan);
      }

      wrap.appendChild(bubble);
      container.appendChild(wrap);

      if (!isMe) {
        playNotificationSound();
      }
    }
    container.scrollTop = container.scrollHeight;
  }

  async function fetchMessages() {
    try {
      const res = await fetch(`/api/messages?after=${lastMessageId}&user=${encodeURIComponent(myNickname)}`);
      if (res.ok) {
        const data = await res.json();
        if (data.messages && data.messages.length > 0) {
          for (const msg of data.messages) {
            renderMessage(msg);
            lastMessageId = Math.max(lastMessageId, msg.id);
          }
        }
        if (data.online_count !== undefined) {
          onlineCount.textContent = `${data.online_count} online`;
        }
      }
    } catch(err) {
    } finally {
      setTimeout(fetchMessages, 800);
    }
  }

  async function sendMessageToServer(text, isSystem = false) {
    if (!myNickname) return;
    try {
      await fetch('/api/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user: myNickname, text: text, system: isSystem })
      });
    } catch(e) {
      console.error('Failed to send:', e);
    }
  }

  async function handleSend(e) {
    e.preventDefault();
    if (!myNickname) {
      openNickModal();
      return;
    }

    const text = input.value.trim();
    if (!text && !selectedFile) return;

    if (selectedFile) {
      const fileToUpload = selectedFile;
      const caption = text;
      clearAttachment();
      input.value = '';

      sendBtn.disabled = true;
      sendBtn.textContent = 'Uploading...';

      try {
        const uploadUrl = `/api/upload?name=${encodeURIComponent(fileToUpload.name)}&user=${encodeURIComponent(myNickname)}&caption=${encodeURIComponent(caption)}`;
        const res = await fetch(uploadUrl, {
          method: 'POST',
          body: fileToUpload
        });
        if (!res.ok) {
          alert('Upload failed: ' + res.statusText);
        }
      } catch (err) {
        alert('Upload error: ' + err);
      } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';
        input.focus();
      }
    } else {
      input.value = '';
      sendMessageToServer(text, false);
      input.focus();
    }
  }

  // Initialization
  if (!myNickname) {
    openNickModal();
  } else {
    displayNick.textContent = myNickname;
    sendMessageToServer(`* ${myNickname} connected *`, true);
  }

  fetchMessages();
</script>
</body>
</html>
"""

class LANChatHTTPHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress noisy HTTP polling logs
        pass

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            content = HTML_PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        # Serve uploaded files: /uploads/<filename>
        if path.startswith("/uploads/"):
            filename = os.path.basename(urllib.parse.unquote(path[len("/uploads/"):]))
            safe_path = os.path.abspath(os.path.join(UPLOADS_DIR, filename))
            if not safe_path.startswith(os.path.abspath(UPLOADS_DIR)) or not os.path.isfile(safe_path):
                self.send_response(404)
                self.end_headers()
                return

            file_size = os.path.getsize(safe_path)
            content_type, _ = mimetypes.guess_type(safe_path)
            if not content_type:
                content_type = "application/octet-stream"

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()

            # Stream file in chunks
            with open(safe_path, 'rb') as f:
                while chunk := f.read(65536):
                    self.wfile.write(chunk)
            return

        if path == "/api/messages":
            query = parse_qs(parsed.query)
            after_id = int(query.get("after", ["0"])[0])
            user = query.get("user", [""])[0]

            now = time.time()
            with lock:
                if user:
                    active_users[user] = now
                # Cleanup users inactive for > 20s
                cutoff = now - 20
                for u in list(active_users.keys()):
                    if active_users[u] < cutoff:
                        del active_users[u]

                # Filter messages after after_id
                new_msgs = [m for m in messages if m["id"] > after_id]
                online_c = max(1, len(active_users))

            resp_data = {
                "messages": new_msgs,
                "online_count": online_c
            }
            body = json.dumps(resp_data).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        global message_id_counter
        parsed = urlparse(self.path)

        if parsed.path == "/api/send":
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length).decode('utf-8')
            try:
                data = json.loads(raw_body)
                user = data.get("user", "Anonymous").strip()[:25]
                text = data.get("text", "").strip()[:1000]
                is_system = bool(data.get("system", False))

                if text:
                    with lock:
                        message_id_counter += 1
                        msg_item = {
                            "id": message_id_counter,
                            "user": user,
                            "text": text,
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "system": is_system,
                            "file": None
                        }
                        messages.append(msg_item)
                        if len(messages) > 500:
                            messages.pop(0)

                        active_users[user] = time.time()

                    if is_system:
                        print(f"[{msg_item['time']}] {text}")
                    else:
                        print(f"[{msg_item['time']}] {user}: {text}")

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(f'{{"error":"{str(e)}"}}'.encode('utf-8'))
            return

        # Upload endpoint: POST /api/upload?name=...&user=...&caption=...
        if parsed.path == "/api/upload":
            query = parse_qs(parsed.query)
            original_filename = query.get("name", ["file.bin"])[0]
            user = query.get("user", ["Anonymous"])[0].strip()[:25]
            caption = query.get("caption", [""])[0].strip()[:1000]

            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 50 * 1024 * 1024:
                self.send_response(413)
                self.end_headers()
                self.wfile.write(b'{"error":"File too large (max 50MB)"}')
                return

            # Sanitize filename
            clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', os.path.basename(original_filename))
            timestamp_prefix = datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_filename = f"{timestamp_prefix}_{clean_name}"
            saved_filepath = os.path.join(UPLOADS_DIR, saved_filename)

            # Read and save file content
            bytes_left = content_length
            with open(saved_filepath, "wb") as f:
                while bytes_left > 0:
                    chunk_size = min(bytes_left, 65536)
                    chunk = self.rfile.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_left -= len(chunk)

            # Determine category
            ext = os.path.splitext(clean_name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp']:
                file_type = 'image'
            elif ext in ['.mp4', '.webm', '.mov', '.ogg']:
                file_type = 'video'
            elif ext in ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac']:
                file_type = 'audio'
            else:
                file_type = 'document'

            file_size_formatted = format_size(content_length)

            file_info = {
                "url": f"/uploads/{saved_filename}",
                "name": original_filename,
                "size": file_size_formatted,
                "type": file_type
            }

            with lock:
                message_id_counter += 1
                msg_item = {
                    "id": message_id_counter,
                    "user": user,
                    "text": caption,
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "system": False,
                    "file": file_info
                }
                messages.append(msg_item)
                if len(messages) > 500:
                    messages.pop(0)

                active_users[user] = time.time()

            print(f"[{msg_item['time']}] {user} shared file: {original_filename} ({file_size_formatted})")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "file": file_info}).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

def run_server():
    local_ip = get_local_ip()
    server_address = ('0.0.0.0', PORT)
    httpd = http.server.ThreadingHTTPServer(server_address, LANChatHTTPHandler)

    print("=" * 65)
    print(" LAN WEB CHAT & FILE SHARING RUNNING")
    print("=" * 65)
    print(" Local Wi-Fi URL:  http://" + local_ip + ":" + str(PORT))
    print(" Uploads folder:   " + UPLOADS_DIR)
    print(" Attachments:      Images, Videos, Audio, PDFs, ZIP, Code, etc.")
    print("=" * 65)
    print("Chat logs will appear below. Press Ctrl+C to stop.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web chat server...")
    finally:
        httpd.server_close()
        print("Web chat stopped.")

if __name__ == '__main__':
    run_server()
