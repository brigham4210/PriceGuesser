"""PriceGuesser for iOS.

Runs the Flask game (copied into the ``pgweb`` package by sync_webapp.sh) on
127.0.0.1 inside the app and shows it in a web view. Zillow links open in Safari.
"""

import logging
import os
import secrets
import socket
import sys
import threading
import webbrowser

import toga
from toga.style import Pack

log = logging.getLogger(__name__)

# A fixed port keeps the web view's origin the same between launches, so the
# best score and photo view saved in localStorage survive restarts.
PREFERRED_PORT = 8765
LOCAL_PREFIX = "http://127.0.0.1:"


def _secret_key(data_dir):
    """Keep one secret key per install so the session cookie survives restarts."""
    path = os.path.join(data_dir, "secret_key")
    try:
        with open(path, encoding="ascii") as f:
            key = f.read().strip()
        if key:
            return key
    except OSError:
        pass
    key = secrets.token_hex(32)
    try:
        with open(path, "w", encoding="ascii") as f:
            f.write(key)
    except OSError:
        pass
    return key


def _port_is_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def start_server(data_dir):
    """Start the game server in a background thread and return its port."""
    import pgweb

    sys.path.insert(0, os.path.dirname(pgweb.__file__))
    os.environ.setdefault("SECRET_KEY", _secret_key(data_dir))

    from werkzeug.serving import make_server

    from main import app

    port = PREFERRED_PORT if _port_is_free(PREFERRED_PORT) else 0
    server = make_server("127.0.0.1", port, app, threaded=True)
    threading.Thread(target=server.serve_forever, name="priceguesser-server", daemon=True).start()
    return server.server_port


class PriceGuesser(toga.App):
    def startup(self):
        self.main_window = toga.MainWindow(title=self.formal_name)
        try:
            self.paths.data.mkdir(parents=True, exist_ok=True)
            port = start_server(str(self.paths.data))
        except Exception:
            log.exception("Couldn't start the game server")
            self.main_window.content = toga.Label(
                "The game couldn't start. Close the app and try again.",
                style=Pack(margin=20),
            )
        else:
            web = toga.WebView(
                url=f"{LOCAL_PREFIX}{port}/",
                on_navigation_starting=self.on_navigation_starting,
                style=Pack(flex=1),
            )
            # Swipe from the edge to go back, like Safari.
            web._impl.native.allowsBackForwardNavigationGestures = True
            self.main_window.content = web
        self.main_window.show()

    def on_navigation_starting(self, widget, url, **kwargs):
        """Game pages stay in the app; other web links open in Safari."""
        if url.startswith(LOCAL_PREFIX) or not url.startswith(("http://", "https://")):
            return True
        webbrowser.open(url)
        return False


def main():
    return PriceGuesser()
