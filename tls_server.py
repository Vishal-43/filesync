import socket
import ssl
import threading
import json
import os

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

            response = {"type": "ack", "status": "ok"}
            tls_conn.send(json.dumps(response).encode("utf-8"))
            print(f"Sent acknowledgment to {client_address}")
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