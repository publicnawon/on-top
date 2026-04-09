from __future__ import annotations

from pathlib import Path

from flask import Flask, send_from_directory


BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")


@app.get("/")
def serve_root():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/<path:requested_path>")
def serve_static(requested_path: str):
    candidate = (BASE_DIR / requested_path).resolve()
    if str(candidate).startswith(str(BASE_DIR.resolve())) and candidate.is_file():
        return send_from_directory(BASE_DIR, requested_path)
    return send_from_directory(BASE_DIR, "index.html")

