"""Run the PriceGuesser Flask app inside the Android app.

The Java activity calls start(), then shows http://127.0.0.1:<port>/ in a WebView.
"""

import os
import secrets
import socket
import sys
import threading

# A fixed port keeps the WebView's origin the same between launches, so the
# best score saved in localStorage survives restarts.
PREFERRED_PORT = 8765

_lock = threading.Lock()
_port = None


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


def start(data_dir):
    """Start the server once and return its port."""
    global _port
    with _lock:
        if _port is not None:
            return _port

        import priceguesser

        sys.path.insert(0, os.path.dirname(priceguesser.__file__))
        os.environ.setdefault("SECRET_KEY", _secret_key(data_dir))

        from werkzeug.serving import make_server

        from main import app

        port = PREFERRED_PORT if _port_is_free(PREFERRED_PORT) else 0
        server = make_server("127.0.0.1", port, app, threaded=True)
        threading.Thread(target=server.serve_forever, name="priceguesser-server", daemon=True).start()
        _port = server.server_port
        return _port
