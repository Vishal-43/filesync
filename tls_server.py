import socket
import ssl
import threading
import json
import os
from config import get_config
from sync_core import scan_dir

CERT_DIR = os.path.expanduser('~/sync-certs')
SERVER_CERT = os.path.join(CERT_DIR, 'linux.crt')
SERVER_KEY = os.path.join(CERT_DIR, 'linux.key')
PEER_CERT = os.path.join(CERT_DIR, 'android.crt')

if not os.path.exists(CERT_DIR):
    raise SystemExit(f"Certificate directory '{CERT_DIR}' does not exist.")
if not os.path.isfile(SERVER_CERT):
    raise SystemExit(f"Server certificate '{SERVER_CERT}' does not exist.")
if not os.path.isfile(SERVER_KEY):
    raise SystemExit(f"Server key '{SERVER_KEY}' does not exist.")
if not os.path.isfile(PEER_CERT):
    raise SystemExit(f"Peer certificate '{PEER_CERT}' does not exist.")

print(f"Using server certificate: {SERVER_CERT}")


context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(SERVER_CERT, SERVER_KEY)
context.load_verify_locations(PEER_CERT)
context.check_hostname = False
context.verify_mode = ssl.CERT_REQUIRED

print("ssl context created with server certificate and peer verification.")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("0.0.0.0", 5555))
server_socket.listen(5)
print("Server listening on port 5555...")


def handle_client(client_socket, client_address):
    print(f"handling client {client_address}")
    try:
        with context.wrap_socket(client_socket, server_side=True) as tls_conn:
            data = tls_conn.recv(4096)
            message = json.loads(data.decode("utf-8"))
            print(f"Received message from {client_address}: {message}")

            response = None

            if message.get("type") == "list":
                cfg = get_config()
                local_dir = cfg['local_dir']
                files = scan_dir(local_dir)
                response = {"type": "list_response", "files": files}
                print(f"sending {len(files)} files to {client_address}")

            elif message.get('type') == "push":
                path = message.get('path')
                size = message.get('size')
                mtime = message.get('mtime') 

                cfg = get_config()
                local_dir = cfg['local_dir']
                abs_path = os.path.join(local_dir, path)

                os.makedirs(os.path.dirname(abs_path), exist_ok=True)

                temp_path = abs_path + ".part"
                with open(temp_path, "wb") as f:
                    recvived = 0
                    while recvived < size:
                        chunk = tls_conn.recv(min(8192, size - recvived))
                        if not chunk:
                            break
                        f.write(chunk)
                        recvived += len(chunk)
                if recvived != size:
                    print(f"[{client_address}] ERROR: size mismatch. Expected {size}, got {recvived}")
                    response = {"type": "error", "message": "size_mismatch"}
                else:
                    os.replace(temp_path, abs_path)
                   
                    if mtime is not None:
                        try:
                            os.utime(abs_path, (mtime, mtime))
                        except Exception as e:
                            print(f"[{client_address}] warning: could not set mtime for {path}: {e}")
                    print(f"[{client_address}],File saved: {path}")
                    response = {"type": "ack", "message": "push ok"}

            elif message.get("type") == "pull":
                path = message.get("path")
                cfg = get_config()
                local_dir = cfg['local_dir']
                abs_path = os.path.join(local_dir, path)

                if not os.path.exists(abs_path):
                    response = {"type": "error", "message": f"file not found: {path}"}
                    print(f"[{client_address}] ERROR: {path} not found")
                else:
                    size = os.path.getsize(abs_path)
                    mtime = os.path.getmtime(abs_path)
                    print(f"[{client_address}] Sending {path} ({size} bytes)")

                    # send metadata first
                    meta = {"type": "pull_response", "path": path, "size": size, "mtime": mtime}
                    tls_conn.send(json.dumps(meta).encode("utf-8"))

                    # stream file
                    with open(abs_path, 'rb') as f:
                        while True:
                            chunk = f.read(8192)
                            if not chunk:
                                break
                            tls_conn.send(chunk)

                    print(f"[{client_address}] ✓ File sent: {path}")
                    response = None  

            else:
                response = {"type": "ack", "message": "ok"}

            if response is not None:
                tls_conn.send(json.dumps(response).encode("utf-8"))
                print(f"sent response to {client_address}")
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()
        print(f"Connection closed for {client_address}")
try:
    while True:
        print("waiting for client connection...")
        client_socket, client_address = server_socket.accept()
        print(f"Connection accepted from {client_address}")


        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.daemon = True
        client_thread.start()
except KeyboardInterrupt:
    print("Server shutting down...")
    server_socket.close()