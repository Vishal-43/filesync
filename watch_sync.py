import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import get_config
from sync_core import scan_dir
from tls_client import (
    make_client_context,
    get_cert,
    request_list,
    compute_actions,
    sync,
)


class DebouncedHandler(FileSystemEventHandler):
    def __init__(self, on_change, debounce_sec=0.8):
        super().__init__()
        self.on_change = on_change
        self.debounce_sec = debounce_sec
        self._timer = None
        self._lock = threading.Lock()

    def on_any_event(self, event):
        if event.is_directory:
            return
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(self.debounce_sec, self.on_change)
            self._timer.daemon = True
            self._timer.start()


def main():
    cfg = get_config()
    local_dir = cfg["local_dir"]
    host = cfg["peer"]["host"]
    port = cfg["peer"]["port"]
    debounce_sec = cfg.get("debounce_ms", 800) / 1000.0
    skew_sec = cfg.get("mtime_skew_sec", 2)
    context = make_client_context(*get_cert())

    def do_sync():
        try:
            r_files = request_list(host, port, context)
            l_files = scan_dir(local_dir)
            actions = compute_actions(l_files, r_files, skew_sec=skew_sec)
            if actions["push"] or actions["pull"]:
                print(f"Sync triggered: push={len(actions['push'])}, pull={len(actions['pull'])}")
                sync(host, port, context, local_dir, actions)
            else:
                print("No changes to sync.")
        except Exception as e:
            print(f"Sync error: {e}")

    handler = DebouncedHandler(do_sync, debounce_sec=debounce_sec)
    observer = Observer()
    observer.schedule(handler, local_dir, recursive=True)
    observer.start()
    print(f"Watching {local_dir} for changes. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
