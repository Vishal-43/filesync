# FileSync

A secure, peer-to-peer file synchronization tool that enables real-time bidirectional file syncing between devices using TLS encryption and file watching. Perfect for syncing files between Linux servers, Android devices (via Termux), or any device running Python.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Linux](#linux)
  - [Termux (Android)](#termux-android)
  - [macOS](#macos)
  - [Windows](#windows)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Starting the Server](#starting-the-server)
  - [Starting the Client with File Watching](#starting-the-client-with-file-watching)
  - [Interactive TUI](#interactive-tui)
- [Architecture](#architecture)
- [Certificate Setup](#certificate-setup)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

✅ **Secure P2P Synchronization** - TLS/SSL encrypted communication between peers  
✅ **Bidirectional Sync** - Push and pull file changes automatically  
✅ **Real-time File Watching** - Automatic sync triggers on file modifications  
✅ **Intelligent Conflict Resolution** - Handles file conflicts based on timestamps and size  
✅ **Debouncing** - Prevents excessive syncs during rapid file changes  
✅ **Cross-Platform** - Runs on Linux, Termux, macOS, and Windows  
✅ **Interactive TUI** - Terminal user interface for monitoring and manual syncing  
✅ **Configuration-based** - JSON config for easy setup and management  

---

## Requirements

- **Python 3.8 or higher**
- **pip** (Python package manager)
- TLS certificates (self-signed or CA-signed)
- Network connectivity between devices

---

## Installation

### Linux

#### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/file-sync.git
cd file-sync
```

#### Step 2: Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/macOS
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install watchdog textual ssl
```

#### Step 4: Generate TLS Certificates
```bash
mkdir -p ~/sync-certs
cd ~/sync-certs

# Generate server certificates
openssl genrsa -out linux.key 2048
openssl req -new -x509 -key linux.key -out linux.cert -days 365

# Generate client certificates
openssl genrsa -out android.key 2048
openssl req -new -x509 -key android.key -out android.cert -days 365
```

#### Step 5: Configure the Application
Edit `sync_config.json`:
```json
{
  "local_dir": "/path/to/your/sync/folder",
  "peer": {
    "host": "192.168.x.x",
    "port": 5555
  },
  "certs": {
    "cert": "/home/username/sync-certs/linux.cert",
    "key": "/home/username/sync-certs/linux.key",
    "peer_cert": "/home/username/sync-certs/android.cert"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 5555
  },
  "debounce_ms": 800,
  "mtime_skew_sec": 2,
  "max_concurrency": 1
}
```

---

### Termux (Android)

#### Step 1: Install Termux
Download and install [Termux](https://termux.com/) from F-Droid or Google Play Store.

#### Step 2: Update and Install Dependencies
```bash
pkg update && pkg upgrade
pkg install python3 openssl git
```

#### Step 3: Clone Repository
```bash
git clone https://github.com/yourusername/file-sync.git
cd file-sync
```

#### Step 4: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 5: Install Python Dependencies
```bash
pip install --upgrade pip
pip install watchdog textual ssl
```

#### Step 6: Generate Certificates
```bash
mkdir -p ~/sync-certs
cd ~/sync-certs

openssl genrsa -out android.key 2048
openssl req -new -x509 -key android.key -out android.cert -days 365
```

#### Step 7: Copy Certificates from Linux
Transfer the Linux certificates to Termux:
```bash
# On Linux
scp ~/sync-certs/linux.cert user@android-ip:~/sync-certs/
scp ~/sync-certs/linux.key user@android-ip:~/sync-certs/

# Or use any file transfer method (Syncthing, SFTP, etc.)
```

#### Step 8: Configure sync_config.json
Adjust paths for Termux storage:
```json
{
  "local_dir": "/storage/emulated/0/Documents/sync_folder",
  "peer": {
    "host": "your-linux-ip",
    "port": 5555
  },
  "certs": {
    "cert": "/data/data/com.termux/files/home/sync-certs/android.cert",
    "key": "/data/data/com.termux/files/home/sync-certs/android.key",
    "peer_cert": "/data/data/com.termux/files/home/sync-certs/linux.cert"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 5555
  },
  "debounce_ms": 800,
  "mtime_skew_sec": 2,
  "max_concurrency": 1
}
```

---

### macOS

#### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/file-sync.git
cd file-sync
```

#### Step 2: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install watchdog textual ssl
```

#### Step 4: Generate Certificates
```bash
mkdir -p ~/sync-certs
cd ~/sync-certs

openssl genrsa -out macos.key 2048
openssl req -new -x509 -key macos.key -out macos.cert -days 365
```

#### Step 5: Configure Application
Update `sync_config.json` with your macOS paths (usually in `/Users/username/...`)

---

### Windows

#### Step 1: Install Python
Download Python 3.8+ from [python.org](https://www.python.org/downloads/)

#### Step 2: Clone Repository
```bash
git clone https://github.com/yourusername/file-sync.git
cd file-sync
```

#### Step 3: Create Virtual Environment
```cmd
python -m venv venv
venv\Scripts\activate
```

#### Step 4: Install Dependencies
```cmd
pip install watchdog textual ssl
```

#### Step 5: Generate Certificates (Using Git Bash or WSL)
```bash
mkdir %USERPROFILE%\sync-certs
cd %USERPROFILE%\sync-certs

openssl genrsa -out windows.key 2048
openssl req -new -x509 -key windows.key -out windows.cert -days 365
```

#### Step 6: Configure Application
Update `sync_config.json` with Windows paths (e.g., `C:\Users\username\sync_folder`)

---

## Configuration

### Config File Structure (`sync_config.json`)

| Property | Type | Description |
|----------|------|-------------|
| `local_dir` | string | Absolute path to the directory to sync |
| `peer.host` | string | IP address of the peer device |
| `peer.port` | number | Port number for peer connection (default: 5555) |
| `certs.cert` | string | Path to your certificate file |
| `certs.key` | string | Path to your private key file |
| `certs.peer_cert` | string | Path to the peer's certificate |
| `server.host` | string | Server bind address (0.0.0.0 for all interfaces) |
| `server.port` | number | Server listen port (default: 5555) |
| `debounce_ms` | number | File change debounce delay in milliseconds (default: 800) |
| `mtime_skew_sec` | number | Time tolerance for file modifications in seconds (default: 2) |
| `max_concurrency` | number | Maximum concurrent file transfers (default: 1) |

---

## Usage

### Starting the Server

On the device with files to share:

```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Run the server
python tls_server.py
```

Expected output:
```
Using server certificate: /home/user/sync-certs/linux.crt
SSL context created with server certificate and peer verification.
Server listening on port 5555...
```

### Starting the Client with File Watching

On the client device:

```bash
# Activate virtual environment first
source venv/bin/activate

# Run the file watcher and sync daemon
python watch_sync.py
```

The client will automatically:
- Scan for local file changes
- Request remote file list
- Push/pull files as needed
- Debounce rapid changes

### Interactive TUI

Launch the terminal user interface for real-time monitoring:

```bash
python tui.py
```

**Controls:**
- `s` - Trigger manual sync
- `q` - Quit application
- `c` - Clear logs

---

## Architecture

### Core Components

1. **`sync_core.py`** - Core synchronization logic
   - File scanning and hashing
   - Entry computation
   - Directory traversal

2. **`tls_server.py`** - Server component
   - Listens for client requests
   - Handles file push/pull operations
   - Manages TLS connections

3. **`tls_client.py`** - Client component
   - Connects to server
   - Requests file lists
   - Computes sync actions
   - Executes file transfers

4. **`watch_sync.py`** - Real-time file watcher
   - Uses `watchdog` to monitor file system
   - Triggers sync on changes
   - Debounces rapid modifications

5. **`tui.py`** - Terminal user interface
   - Interactive dashboard
   - Status monitoring
   - Log display
   - Manual sync trigger

6. **`config.py`** - Configuration management
   - Loads/saves JSON configuration
   - Manages certificates and peer info

---

## Certificate Setup

### Generate Self-Signed Certificates

For quick testing, generate self-signed certificates:

```bash
mkdir -p certs
cd certs

# Server certificate
openssl genrsa -out server.key 2048
openssl req -new -x509 -key server.key -out server.crt -days 365

# Client certificate
openssl genrsa -out client.key 2048
openssl req -new -x509 -key client.key -out client.crt -days 365
```

### Import Certificates in config.json

Update paths in your configuration file to point to generated certificates.

**Security Note:** Self-signed certificates are suitable for private networks. For production, use certificates from a trusted Certificate Authority.

---

## Troubleshooting

### Certificate Not Found
```
SystemExit: Certificate directory '~/sync-certs' does not exist.
```
**Solution:** Ensure the `~/sync-certs` directory exists and contains all required certificates.

### Connection Refused
```
ConnectionRefusedError: [Errno 111] Connection refused
```
**Solution:** 
- Verify server is running: `python tls_server.py`
- Check firewall settings allow port 5555
- Ensure correct IP and port in `sync_config.json`

### Size Mismatch Error
```
[ERROR]: size mismatch. Expected X, got Y
```
**Solution:** Network interruption occurred. File transfer will retry on next sync.

### Permission Denied on Termux
```
PermissionError: [Errno 13] Permission denied
```
**Solution:** Grant storage permissions to Termux or adjust `local_dir` to accessible storage location.

### Files Not Syncing
- Check if file watcher is running: `ps aux | grep watch_sync.py`
- Verify network connectivity between devices
- Check file permissions and disk space
- Review logs in TUI application

---

## Project Structure

```
file-sync/
├── sync_core.py          # Core sync logic
├── tls_server.py         # Server component
├── tls_client.py         # Client component  
├── watch_sync.py         # File watcher daemon
├── tui.py                # Terminal UI
├── config.py             # Configuration manager
├── sync_config.json      # Configuration file
├── README.md             # This file
└── requirements.txt      # Python dependencies
```

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Security Considerations

- ✅ All communication is TLS-encrypted
- ✅ Mutual certificate authentication between peers
- ✅ No credentials stored in plain text
- ⚠️ Use strong certificates in production environments
- ⚠️ Restrict network access to trusted devices only
- ⚠️ Regularly update Python and dependencies

---

## Performance Tips

1. **Debounce Tuning** - Adjust `debounce_ms` based on your file change frequency
2. **Concurrency** - Increase `max_concurrency` for faster multi-file transfers
3. **Time Skew** - Set `mtime_skew_sec` based on network/system clock differences
4. **File Monitoring** - Exclude large unnecessary directories from sync

---

## License

This project is licensed under the MIT License - see LICENSE file for details.

---

## Support

For issues, questions, or suggestions, please:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section above

---

**Happy Syncing! 🚀**
