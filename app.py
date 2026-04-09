from __future__ import annotations

from pathlib import Path

from flask import Flask, send_from_directory


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "report-web"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")


@app.get("/")
def serve_root():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/<path:requested_path>")
def serve_static(requested_path: str):
    candidate = (STATIC_DIR / requested_path).resolve()
    static_root = STATIC_DIR.resolve()

    if str(candidate).startswith(str(static_root)) and candidate.is_file():
        return send_from_directory(STATIC_DIR, requested_path)

    # SPA fallback: unknown routes still load the app shell.
    return send_from_directory(STATIC_DIR, "index.html")

