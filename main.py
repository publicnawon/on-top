from __future__ import annotations

import mimetypes
from pathlib import Path
from urllib.parse import unquote


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "report-web"


def _resolve_path(raw_path: str) -> Path:
    clean_path = unquote(raw_path.split("?", 1)[0]).lstrip("/")
    if not clean_path:
        clean_path = "index.html"
    requested = (STATIC_DIR / clean_path).resolve()

    if requested.is_dir():
        requested = requested / "index.html"

    if not str(requested).startswith(str(STATIC_DIR.resolve())):
        return STATIC_DIR / "index.html"
    return requested


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    target = _resolve_path(path)

    if not target.exists() or not target.is_file():
        target = STATIC_DIR / "index.html"

    content = target.read_bytes()
    mime, _ = mimetypes.guess_type(str(target))
    content_type = mime or "application/octet-stream"

    start_response(
        "200 OK",
        [
            ("Content-Type", content_type),
            ("Content-Length", str(len(content))),
            ("Cache-Control", "no-cache"),
        ],
    )
    return [content]


if __name__ == "__main__":
    from wsgiref.simple_server import make_server

    host = "127.0.0.1"
    port = 8000
    print(f"Serving on http://{host}:{port}")
    make_server(host, port, app).serve_forever()
