#!/usr/bin/env python3
"""
LAN Chat Server (Command Line)
Allows multiple devices on the same Wi-Fi / Local Network (LAN) to chat.
Uses pure Python standard library (no extra installations required).
"""

import socket
import threading
import sys
from datetime import datetime

HOST = '0.0.0.0'  # Listen on all network interfaces
PORT = 5555        # Port number to listen on

clients = {}       # Maps socket -> nickname
lock = threading.Lock()

def get_local_ip():
    """Detect the local LAN IP address of this machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to an arbitrary external address (does not send packets)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def broadcast(message, sender_sock=None):
    """Send a message to all connected clients except optionally the sender."""
    with lock:
        for client_sock in list(clients.keys()):
            if client_sock != sender_sock:
                try:
                    client_sock.sendall(message.encode('utf-8'))
                except Exception:
                    # Client dropped connection
                    remove_client(client_sock)

def remove_client(client_sock):
    """Remove a client from active list and announce exit."""
    with lock:
        if client_sock in clients:
            nickname = clients[client_sock]
            del clients[client_sock]
            try:
                client_sock.close()
            except Exception:
                pass
            timestamp = datetime.now().strftime('%H:%M:%S')
            leave_msg = f"[{timestamp}] *** {nickname} left the chat. ({len(clients)} online) ***\n"
            print(leave_msg.strip())
            # Broadcast to remaining clients
            for sock in list(clients.keys()):
                try:
                    sock.sendall(leave_msg.encode('utf-8'))
                except Exception:
                    pass

def handle_client(client_sock, client_address):
    """Handles communication with an individual client."""
    nickname = None
    try:
        # First message from client must be their nickname
        client_sock.sendall(b"ENTER_NICKNAME\n")
        raw_nick = client_sock.recv(1024).decode('utf-8').strip()
        if not raw_nick:
            client_sock.close()
            return

        nickname = raw_nick
        with lock:
            clients[client_sock] = nickname

        timestamp = datetime.now().strftime('%H:%M:%S')
        join_msg = f"[{timestamp}] *** {nickname} joined from {client_address[0]}! ({len(clients)} online) ***\n"
        print(join_msg.strip())
        broadcast(join_msg, sender_sock=client_sock)

        # Welcome message to the newly connected user
        welcome = (
            f"--- Connected to LAN Chat Server ---\n"
            f"You are chatting as: {nickname}\n"
            f"Type your message and hit Enter. Type /quit to exit.\n"
            f"------------------------------------\n"
        )
        client_sock.sendall(welcome.encode('utf-8'))

        # Receive messages loop
        while True:
            data = client_sock.recv(4096)
            if not data:
                break
            text = data.decode('utf-8').strip()
            if not text:
                continue

            if text == "/quit":
                break

            timestamp = datetime.now().strftime('%H:%M:%S')
            formatted_msg = f"[{timestamp}] {nickname}: {text}\n"
            print(formatted_msg.strip())
            broadcast(formatted_msg, sender_sock=client_sock)

    except (ConnectionResetError, BrokenPipeError):
        pass
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        remove_client(client_sock)

def main():
    local_ip = get_local_ip()
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow port reuse immediately upon restart
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_sock.bind((HOST, PORT))
        server_sock.listen(20)
    except Exception as e:
        print(f"Failed to start server on {HOST}:{PORT}: {e}")
        sys.exit(1)

    print("=" * 60)
    print(" LAN CHAT SERVER STARTED")
    print("=" * 60)
    print(f" Local Machine IP:  {local_ip}")
    print(f" Listening Port:    {PORT}")
    print("\n Instructions for others on the same Wi-Fi / LAN:")
    print(f" Run client.py and connect to IP: {local_ip}  Port: {PORT}")
    print("=" * 60)
    print("Waiting for incoming connections... (Press Ctrl+C to stop)\n")

    try:
        while True:
            client_sock, client_addr = server_sock.accept()
            t = threading.Thread(target=handle_client, args=(client_sock, client_addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\nShutting down LAN Chat Server...")
    finally:
        with lock:
            for sock in list(clients.keys()):
                try:
                    sock.sendall(b"\n*** Server is shutting down ***\n")
                    sock.close()
                except Exception:
                    pass
            clients.clear()
        server_sock.close()
        print("Server stopped.")

if __name__ == '__main__':
    main()
