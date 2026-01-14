# for client device
import socket 
import ssl
import json
import os
from config import get_config
from sync_core import scan_dir

# CERT_DIR = os.path.expanduser('~/sync-certs')
# CLIENT_CERT = os.path.join(CERT_DIR, 'android.crt')
# CLIENT_KEY = os.path.join(CERT_DIR, 'android.key')
# SERVER_CERT = os.path.join(CERT_DIR, 'linux.crt')


# context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
# context.load_cert_chain(CLIENT_CERT, CLIENT_KEY)
# context.load_verify_locations(SERVER_CERT)
# context.check_hostname = False
# context.verify_mode = ssl.CERT_REQUIRED

# print(f"Using client certificate: {CLIENT_CERT}")


# client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client_socket = context.wrap_socket(client_socket, server_hostname='127.0.0.1')

# print("Connecting to server on port 5555...")
# client_socket.connect(('127.0.0.1',5555))
# print("Connected to server.")

# message = {"type":"list"}
# client_socket.send(json.dumps(message).encode('utf-8'))
# print("Message sent to server.")

# response_data = client_socket.recv(16384)
# resp_dict = json.loads(response_data.decode('utf-8'))
# print(f"recived {len(resp_dict['files'])} files:")
# for f in resp_dict['files']:
#     print(f"File: {f['path']} Size: {f['size']} Mtime: {f['mtime']}") 

# client_socket.close()
# print("connection closed")

def recv_all(client_socket, chunk=8192):
    chunks = []
    while True:
        data = client_socket.recv(chunk)
        if not data:
            break
        chunks.append(data)
    

    return b"".join(chunks)

def make_client_context(CLIENT_CERT,CLIENT_KEY,SERVER_CERT):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_cert_chain(CLIENT_CERT, CLIENT_KEY)
    context.load_verify_locations(SERVER_CERT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_REQUIRED
    return context

def request_list(host,port,context):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with context.wrap_socket(client_socket,server_hostname=host) as tls:
        tls.connect((host,port))
        message = {"type":"list"}
        tls.send(json.dumps(message).encode('utf-8'))
        raw = recv_all(tls)
    resp = json.loads(raw.decode('utf-8'))
    assert resp.get('type') == "list_response", f"unexpected response type: {resp}" 
    return resp["files"]

def get_cert():
    CERT_DIR = os.path.expanduser('~/sync-certs')
    CLIENT_CERT = os.path.join(CERT_DIR, 'android.crt')
    CLIENT_KEY = os.path.join(CERT_DIR, 'android.key')
    SERVER_CERT = os.path.join(CERT_DIR, 'linux.crt')
    if not os.path.exists(CERT_DIR):
        raise SystemExit(f"Certificate directory '{CERT_DIR}' does not exist.")
    if not os.path.isfile(SERVER_CERT):
        raise SystemExit(f"Server certificate '{CLIENT_CERT}' does not exist.")
    if not os.path.isfile(CLIENT_KEY):
        raise SystemExit(f"Client key '{CLIENT_KEY}' does not exist.")
    if not os.path.isfile(SERVER_CERT):
        raise SystemExit(f"Server certificate '{SERVER_CERT}' does not exist.")

    return CLIENT_CERT,CLIENT_KEY,SERVER_CERT
def to_map(entries):
    return {e["path"]:e for e in entries}
def compute_actions(local_files,remote_files,skew_sec=2.0):
    action = {"push":[],"pull":[],"skip":[]}
    L = to_map(local_files)
    R = to_map(remote_files)
    all_paths = set(L) | set(R)
    for p in all_paths:
        le = L.get(p)
        re = R.get(p)
        if le and not re:
            action["push"].append(le)
        elif re and not le:
            action["pull"].append(re)
        else:
            dt = (le["mtime"]-re["mtime"])
            if abs(dt) <=skew_sec:
                action["skip"].append(p)
            elif dt > 0:
                action["push"].append(p)
            else:
                action["pull"].append(p)
    return action

def push(host,port,context, local_file, remote_path):
    size = os.path.getsize(local_file)
    mtime = os.path.getmtime(local_file)
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 
    with context.wrap_socket(s,server_hostname=host) as tls:
        tls.connect((host,port))

        msg = {"type":"push","path":remote_path,"size":size,"mtime":mtime}
        tls.send(json.dumps(msg).encode('utf-8'))
        with open(local_file,'rb') as f:
            sent = 0
            while sent < size:
                chunk = f.read(8192)
                if not chunk:
                    break
                tls.send(chunk)
                sent += len(chunk)

        ack = recv_all(tls)
        resp = json.loads(ack.decode('utf-8'))
        print(f"Push response: {resp}")
        return resp

def pull(host,port,context,remote_path, local_file):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 
    with context.wrap_socket(s,server_hostname=host) as tls:
        tls.connect((host,port))

        msg = {"type":"pull","path":remote_path}
        tls.send(json.dumps(msg).encode("utf-8"))
        print(f"pulling {remote_path} to {local_file}")

        meta_raw = tls.recv(8192)
        meta = json.loads(meta_raw.decode("utf-8"))
        if meta.get("type") == "error":
            print(f"Error from server: {meta.get('message')}")
            return meta
        size = meta.get("size")
        remote_mtime = meta.get("mtime")
        temp_file = local_file + ".part"
        os.makedirs(os.path.dirname(local_file),exist_ok=True)
        with open(temp_file,"wb") as f:
            recived = 0
            while recived < size:
                chunk = tls.recv(8192)
                if not chunk:
                    break
                f.write(chunk)
                recived += len(chunk)
        if recived != size:
            print(f"ERROR: size mismatch. Expected {size}, got {recived}")
            return {"type":"error","message":"size_mismatch"}
        os.replace(temp_file,local_file)
        if remote_mtime is not None:
            try:
                os.utime(local_file, (remote_mtime, remote_mtime))
            except Exception as e:
                print(f"WARNING: could not set mtime for {local_file}: {e}")
       
        print(f"File '{remote_path}' pulled successfully.")
        return local_file
def sync(host,port,context,local_dir,actions):
    push_count,pull_count = 0, 0
    for a in actions["push"]:
        if isinstance(a,dict):
            path = a["path"]
        else:
            path = a

        local_file = os.path.join(local_dir,path)
        if os.path.exists(local_file):
            print(f"Push:{path}")
            push(host,port,context,local_file,path)
            push_count += 1
        else:
            print(f"Push: {path} not found")

    for a in actions["pull"]:
        if isinstance(a,dict):
            path = a["path"]
        else:
            path = a
        local_file = os.path.join(local_dir,path)
        print(f"Pull:{path}")
        pull(host,port,context,path,local_file)
        pull_count += 1
    print(f"Sync complete. Pushed {push_count} files, Pulled {pull_count} files.")
# if __name__ == "__main__":
#     config = get_config()
#     host = config["peer"]["host"]
#     port = config["peer"]["port"]
#     local_dir = config["local_dir"]
#     context = make_client_context(*get_cert())
    
#     print("=" * 50)
#     print("LAN File Sync - Full Test")
#     print("=" * 50)
    
#     # Get file lists
#     print("\n1. Fetching remote file list...")
#     r_files = request_list(host, port, context)
#     print(f"   Remote: {len(r_files)} files")
    
#     print("\n2. Scanning local directory...")
#     l_files = scan_dir(local_dir)
#     print(f"   Local: {len(l_files)} files")
    
#     # Compute actions
#     print("\n3. Computing sync actions...")
#     actions = compute_actions(l_files, r_files, skew_sec=config.get("mtime_skew_sec", 2))
#     print(f"   Actions: {len(actions['push'])} push, {len(actions['pull'])} pull, {len(actions['skip'])} skip")
    
#     # Show samples
#     if actions["push"]:
#         print(f"\n   Sample PUSH files:")
#         for item in actions["push"][:3]:
#             p = item["path"] if isinstance(item, dict) else item
#             print(f"      → {p}")
    
#     if actions["pull"]:
#         print(f"\n   Sample PULL files:")
#         for item in actions["pull"][:3]:
#             p = item["path"] if isinstance(item, dict) else item
#             print(f"      ← {p}")
    
#     # Execute sync
#     print("\n4. Executing sync...")
#     sync(host, port, context, local_dir, actions)
    
#     print("\n" + "=" * 50)
#     print("✓ Sync test complete!")
#     print("=" * 50)