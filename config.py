import json 
import os

CONFIG_FILE = "sync_config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return FileNotFoundError(f"config file '{config_file}' does not exist.")
    
    with open(CONFIG_FILE,"r") as f:
        config = json.load(f)
    
    return config

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config,f,indent=2)

    print(f"config saved to '{CONFIG_FILE}'")


def get_config():
    return load_config()

def set_local_dir(path):
    config = load_config()
    config['local_dir'] = os.path.abspath(path)
    save_config(config)
    print(f"local directory set to:{config['local_dir']}")

def set_peer(host,port):
    config = load_config()
    config['peer']['host'] = host
    config['peer']['port'] = int(port)
    save_config(config)
    print(f"peer set to: {host}:{port}")


def set_certs(cert,key,peer_cert):
    config = load_config()
    config['certs']['cert'] = os.path.abspath(cert)
    config['certs']['key']= os.path.abspath(key)
    config['certs']['peer_cert'] =os.path.abspath(peer_cert)
    save_config(config)
    print("certificates updated in config.")
def reset_config():
    default = {
    "local_dir":"/home/vishal/sync_folder",
    "peer":{
        "host":"192.168.1.101",
        "port":5555
    },
    "certs":{
        "cert":"/home/vishal/sync_certs/linux.cert",
        "key":"/home/vishal/sync_certs/linux.key",
        "peer_cert":"/home/vishal/sync_certs/android.cert"
    },
    "server":{
        "host":"0.0.0.0",
        "port":5555
    },
    "debounce_ms":800,
    "mtime_skew_sec":2,
    "max_concurrency":1
}
    save_config(default)
    print("config reset to defaults")
if __name__ == "__main__":
    cfg = load_config()
    print("current config:")
    print(json.dumps(cfg,indent=2))

    print("test set_peer")
    set_peer("192.168.1.200",6000)

    cfg = get_config()
    print(f"New peer:{cfg['peer']}")

    print("reset config")
    reset_config()