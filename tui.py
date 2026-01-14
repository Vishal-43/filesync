from textual.app import ComposeResult, App
from textual.widgets import Header,Footer,Button,Static,Input,DataTable
from textual.containers import Horizontal,Vertical,Container
from textual.widgets import Header, Footer, Static,Button
from textual.binding import Binding
from textual.reactive import reactive
import asyncio
from config import get_config
from sync_core import scan_dir
from tls_client import request_list, compute_actions, sync, make_client_context, get_cert

class StatusPanel(Static):
    connected = reactive(False)
    last_sync = reactive("Never")

    def render(self) -> str:
        status = "Connected" if self.connected else "Disconnected"
        cfg = get_config()
        return f"""
        [bold]sync Status [/bold]

        status : {status}
        peer: {cfg["peer"]["host"]}:{cfg["peer"]["port"]}
        "last sync: {self.last_sync}
        """

class LogPanel(Static):

    def __init__(self):
        super().__init__()
        self.logs = []

    def add_log(self,message:str):
        self.logs.append(message)
        if len(self.logs) > 100 :
            self.logs.pop(0)
        self.update("\n".join(self.logs[-20:])) 
    def render(self) -> str:
        return "[bold]Log Panel[/bold]\n" + "\n".join(self.logs[-20:])

class SyncApp(App):
    BINDINGS = [
        Binding("s", "sync_files", "Sync Files"),
        Binding("q", "quit", "Quit"),
        Binding("c", "clear_logs", "Clear Logs"),
    ]

    def __init__(self):
        super().__init__()
        self.status_panel = StatusPanel()
        self.log_panel = LogPanel()
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield self.status_panel
            yield self.log_panel
            with Horizontal():
                yield Button("Sync Files", id="sync_button")
                yield Button("Clear Logs", id="clear_button")
                yield Button("Quit", id="quit_button")
        yield Footer()
    

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "sync_button":
            self.action_sync()
        elif event.button.id == "clear_button":
            self.action_clear_logs()
        elif event.button.id == "quit_button":
            self.action_quit()

    def action_sync(self) -> None:
        self.log_panel.add_log("starting sync....")
        asyncio.create_task(self._do_sync())
    
    async def _do_sync(self):
        try:
            cfg = get_config()
            host = cfg["peer"]['host']
            port = cfg["peer"]["port"]
            local_dir =cfg["local_dir"]
            context = make_client_context(*get_cert())

            self.log_panel.add_log(f"Fetching remote file list from {host}:{port}...")
            r_files = request_list(host,port,context)
            self.log_panel.add_log(f"Remote: {len(r_files)} files")

            l_files = scan_dir(local_dir)
            self.log_panel.add_log(f"local: {len(l_files)} files")

            actions = compute_actions(l_files,r_files)
            self.log_panel.add_log(f"Actions: {len(actions['push'])} push, {len(actions['pull'])} pull, {len(actions['skip'])} skip")

            sync(host,port,context,local_dir,actions)
            self.log_panel.add_log("Sync complete.")
            self.status_panel.last_sync = "Just now"
        except Exception as e:
            self.log_panel.add_log(f"Error during sync: {e}")
    def action_clear_logs(self) -> None:
        self.log_panel.logs.clear()
        self.log_panel.update("")
    def action_quit(self) -> None:
        self.exit()
    
if __name__ == "__main__":
    app = SyncApp()
    app.run()
