import os 
import json
from config import get_config
import hashlib

def compute_hash(file_path):
    sha = hashlib.sha256()
    with open(file_path,'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()

def compute_entry(local_dir,abs_path):
    rel_path = os.path.relpath(abs_path,local_dir)
    size = os.stat(abs_path).st_size
    mtime = os.stat(abs_path).st_mtime
    return {'path':rel_path,'size':size,'mtime':mtime}


def scan_dir(local_dir):
    abs_path = os.path.abspath(local_dir)
    entries =[]
    for (root,dirs,files) in os.walk(abs_path):
        for filename in files:
            file_path = os.path.join(root,filename)
            entry = compute_entry(abs_path,file_path)
            entries.append(entry)
    return entries
if __name__ == "__main__":
    cfg = get_config()
    local_dir = cfg['local_dir']
    entries = scan_dir(local_dir)

    if entries:
        for e in entries[:2]:
            print(f"Found file: {e['path']} Size: {e['size']} Mtime: {e['mtime']}")