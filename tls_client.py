# for client device
import socket 
import ssl
import json
import os

CERT_DIR = os.path.expanduser('~/sync-certs')
CLIENT_CERT = os.path.join(CERT_DIR, 'android.crt')
CLIENT_KEY = os.path.join(CERT_DIR, 'android.key')
SERVER_CERT = os.path.join(CERT_DIR, 'linux.crt')


context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.load_cert_chain(CLIENT_CERT, CLIENT_KEY)
context.load_verify_locations(SERVER_CERT)
context.check_hostname = False
context.verify_mode = ssl.CERT_REQUIRED

print(f"Using client certificate: {CLIENT_CERT}")


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket = context.wrap_socket(client_socket, server_hostname='127.0.0.1')

print("Connecting to server on port 5555...")
client_socket.connect(('127.0.0.1',5555))
print("Connected to server.")

message = {"type":"echo","content":"hello from client"}
client_socket.send(json.dumps(message).encode('utf-8'))
print("Message sent to server.")

response_data = client_socket.recv(4096)
print(f"Response from server: {json.loads(response_data.decode('utf-8'))}")

client_socket.close()
print("connection closed")