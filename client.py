#!/usr/bin/env python3
"""
LAN Chat Client (Command Line)
Connects to a LAN Chat Server running on the same network using its IP address.
"""

import socket
import threading
import sys

def receive_messages(sock):
    """Continuously receive incoming messages from the server."""
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                print("\n[Disconnected from server]")
                break
            message = data.decode('utf-8')
            # Print incoming message neatly
            print(f"\r{message}", end="")
            print("> ", end="", flush=True)
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            print("\n[Connection to server lost]")
            break
    sock.close()
    sys.exit(0)

def main():
    print("=" * 50)
    print("        LAN CHAT CLIENT")
    print("=" * 50)

    # Ask for Server IP
    default_ip = "127.0.0.1"
    server_ip = input(f"Enter Server IP Address [{default_ip}]: ").strip()
    if not server_ip:
        server_ip = default_ip

    # Ask for Port
    default_port = 5555
    port_input = input(f"Enter Server Port [{default_port}]: ").strip()
    port = int(port_input) if port_input.isdigit() else default_port

    # Connect to server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print(f"Connecting to {server_ip}:{port}...")
        sock.connect((server_ip, port))
    except Exception as e:
        print(f"Error: Could not connect to {server_ip}:{port} -> {e}")
        print("Please verify the IP address and that the server is currently running.")
        sys.exit(1)

    # Server prompts for nickname
    first_msg = sock.recv(1024).decode('utf-8')
    if "ENTER_NICKNAME" in first_msg:
        while True:
            nickname = input("Enter your chat nickname: ").strip()
            if nickname:
                sock.sendall((nickname + "\n").encode('utf-8'))
                break
            print("Nickname cannot be empty.")

    # Start background receiver thread
    receiver_thread = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    receiver_thread.start()

    # User input loop
    try:
        while True:
            try:
                msg = input()
            except EOFError:
                break

            msg_clean = msg.strip()
            if not msg_clean:
                print("> ", end="", flush=True)
                continue

            if msg_clean.lower() == "/quit":
                sock.sendall(b"/quit\n")
                break

            try:
                sock.sendall((msg_clean + "\n").encode('utf-8'))
                print("> ", end="", flush=True)
            except Exception:
                print("[Failed to send message]")
                break

    except KeyboardInterrupt:
        print("\nExiting chat...")
        try:
            sock.sendall(b"/quit\n")
        except Exception:
            pass
    finally:
        sock.close()
        print("Goodbye!")

if __name__ == '__main__':
    main()
