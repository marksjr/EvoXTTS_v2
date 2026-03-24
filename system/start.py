"""Script de inicializacao da API Evo XTTS V2."""

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser

import uvicorn

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.config import HOST, PORT


def wait_until_ready_and_open_browser() -> None:
    """Abre o navegador somente quando a API responder como pronta."""
    url_host = "localhost" if HOST == "0.0.0.0" else HOST
    health_url = f"http://{url_host}:{PORT}/health"
    app_url = f"http://{url_host}:{PORT}/"
    deadline = time.time() + 300

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=3) as response:
                payload = json.loads(response.read().decode("utf-8"))
                if payload.get("status") == "ok" and payload.get("model_loaded"):
                    webbrowser.open(app_url)
                    return
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            pass
        time.sleep(1.5)


if __name__ == "__main__":
    if os.name == "nt":
        threading.Thread(target=wait_until_ready_and_open_browser, daemon=True).start()

    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=False,
        workers=1,
        log_level="info",
    )
