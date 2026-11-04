"""
Web app backend for the YTS movie selector.

Serves the single-page UI and the selection API. The browser queries the
YTS API directly (the API is CORS-enabled: access-control-allow-origin: *);
when the YTS mirrors are unreachable from the browser's network, the UI falls
back to the /api/movies and /api/img endpoints below, which fetch through the
SSH SOCKS5 tunnel pool (CTFILE_PROXY_HOSTS) when direct access also fails.

Only https/yts-allowlisted hosts are proxied, and each target hostname is
resolved and checked against loopback/private/reserved address ranges before
any request is made.

Usage:
    uv run python skills/yts/scripts/movie_selector_server.py
    uv run python skills/yts/scripts/movie_selector_server.py --port 8010 --host 127.0.0.1
"""

import argparse
import atexit
import ipaddress
import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
import uvicorn
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Route

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

import movie_selection_store as store  # noqa: E402

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "skills" / "tvboxnow" / "scripts"))

from ssh_proxy_pool import ProxyPool, parse_hosts  # noqa: E402

INDEX_HTML = Path(__file__).resolve().parents[1] / "assets" / "movie_selector" / "index.html"

YTS_HOSTS = {"yts.mx", "yts.lt", "yts.gg", "movies-api.accel.li"}

_pool: ProxyPool | None = None


def _get_pool() -> ProxyPool | None:
    """Lazily start the SOCKS tunnel pool (one ssh -D tunnel per configured host)."""
    global _pool
    if _pool is not None:
        return _pool
    hosts = parse_hosts(os.environ.get("CTFILE_PROXY_HOSTS", ""))
    if not hosts:
        return None
    _pool = ProxyPool(hosts)
    atexit.register(_pool.stop)
    urls = _pool.start()
    print(f"[progress] proxy pool: {len(urls)} tunnel(s) up "
          f"({', '.join(hosts)})" if urls else "[progress] no tunnels came up; "
          "backend YTS proxy will go direct")
    return _pool


def _proxy_kwargs() -> dict:
    """requests kwargs routing through the tunnel pool (None -> direct)."""
    pool = _get_pool()
    url = pool.next() if pool else None
    if url:
        return {"proxies": {"http": url, "https": url}}
    return {}


PROXY_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def _fetch_yts_json(params: dict) -> dict:
    """Fetch list_movies.json (threadpool offloaded). URL is a fixed, allowlisted
    YTS endpoint, re-validated inline immediately before the request."""
    url = "https://yts.gg/api/v2/list_movies.json"  # fixed allowlisted endpoint
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.hostname not in YTS_HOSTS:
        raise ValueError(f"blocked non-allowlisted request target: {url}")
    for info in socket.getaddrinfo(parsed.hostname, 443, proto=socket.IPPROTO_TCP):
        addr = ipaddress.ip_address(info[4][0])
        if (addr.is_loopback or addr.is_private or addr.is_link_local
                or addr.is_reserved or addr.is_multicast or addr.is_unspecified):
            raise ValueError(f"blocked private/resolved address for {parsed.hostname}: {addr}")
    resp = requests.get(url, params=params, timeout=30,
                        headers=PROXY_UA, **_proxy_kwargs())
    resp.raise_for_status()
    return resp.json()


def _fetch_image(target: str) -> tuple[bytes, str]:
    """Fetch an image (threadpool offloaded). The target is validated inline:
    http(s) only, allowlisted host only, resolved IPs must be public."""
    parsed = urlparse(target)
    if parsed.scheme not in ("http", "https") or (parsed.hostname or "") not in YTS_HOSTS:
        raise ValueError(f"blocked non-allowlisted image host: {target[:100]}")
    try:
        infos = socket.getaddrinfo(parsed.hostname, 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        infos = []  # allowlist is authoritative when local DNS cannot resolve
    for info in infos:
        addr = ipaddress.ip_address(info[4][0])
        if (addr.is_loopback or addr.is_private or addr.is_link_local
                or addr.is_reserved or addr.is_multicast or addr.is_unspecified):
            raise ValueError(f"blocked private/reserved address for {parsed.hostname}: {addr}")
    resp = requests.get(target, timeout=30, headers=PROXY_UA, **_proxy_kwargs())
    resp.raise_for_status()
    media_type = resp.headers.get("content-type", "image/jpeg")
    if not media_type.startswith("image/"):
        raise ValueError(f"not an image: {media_type}")
    return resp.content, media_type


async def proxy_movies(request: Request) -> JSONResponse:
    """Proxy list_movies.json through the tunnel pool (browser direct-fetch fallback)."""
    allowed = {"query_term", "genre", "minimum_rating", "sort_by", "order_by",
               "page", "limit", "with_images", "with_cast"}
    params = {k: v for k, v in request.query_params.items() if k in allowed}
    try:
        data = await run_in_threadpool(_fetch_yts_json, params)
        return JSONResponse(data)
    except (ValueError, requests.RequestException) as exc:
        return JSONResponse({"error": f"YTS proxy failed: {exc}"}, status_code=502)


async def proxy_image(request: Request) -> Response:
    """Proxy a YTS-hosted image (poster/screencap) for browsers that cannot reach it."""
    target = request.query_params.get("u", "")
    try:
        content, media_type = await run_in_threadpool(_fetch_image, target)
        return Response(content, media_type=media_type,
                        headers={"Cache-Control": "public, max-age=86400"})
    except (ValueError, requests.RequestException) as exc:
        return Response(f"image proxy failed: {exc}", status_code=502)


async def index(request: Request) -> FileResponse:
    return FileResponse(INDEX_HTML, media_type="text/html")


async def get_selection(request: Request) -> JSONResponse:
    status = request.query_params.get("status")
    if status and status not in store.VALID_STATUSES:
        return JSONResponse({"error": f"invalid status: {status}"}, status_code=400)
    return JSONResponse({"selected": store.list_selections(status)})


async def add_selection(request: Request) -> JSONResponse:
    try:
        movie = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    if not isinstance(movie, dict) or movie.get("id") is None or not movie.get("title"):
        return JSONResponse({"error": "movie must include id and title"}, status_code=400)
    torrents = movie.get("torrents")
    if torrents is not None and not isinstance(torrents, list):
        return JSONResponse({"error": "torrents must be a list"}, status_code=400)
    item = store.add_selection(movie)
    print(f"[progress] queued: {item['title']} ({item.get('year')}) "
          f"-> {len(item.get('torrents') or [])} torrent(s)")
    return JSONResponse({"added": item, "selected": store.list_selections()})


async def remove_selection(request: Request) -> JSONResponse:
    movie_id = request.path_params["movie_id"]
    removed = store.remove_selection(movie_id)
    return JSONResponse({"removed": removed, "selected": store.list_selections()})


async def clear_selection(request: Request) -> JSONResponse:
    removed = store.clear_selections()
    print(f"[progress] cleared {removed} selection(s)")
    return JSONResponse({"removed": removed, "selected": []})


async def set_status(request: Request) -> JSONResponse:
    movie_id = request.path_params["movie_id"]
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    status = body.get("status")
    if status not in store.VALID_STATUSES:
        return JSONResponse({"error": f"status must be one of {sorted(store.VALID_STATUSES)}"},
                            status_code=400)
    item = store.set_status(movie_id, status)
    if item is None:
        return JSONResponse({"error": f"movie {movie_id} not in selection"}, status_code=404)
    return JSONResponse({"updated": item, "selected": store.list_selections()})


routes = [
    Route("/", index),
    Route("/api/movies", proxy_movies),
    Route("/api/img", proxy_image),
    Route("/api/selection", get_selection, methods=["GET"]),
    Route("/api/selection", add_selection, methods=["POST"]),
    Route("/api/selection/clear", clear_selection, methods=["POST"]),
    Route("/api/selection/{movie_id:int}", remove_selection, methods=["DELETE"]),
    Route("/api/selection/{movie_id:int}/status", set_status, methods=["POST"]),
]

app = Starlette(routes=routes)


def main() -> None:
    parser = argparse.ArgumentParser(description="YTS movie selector web app backend")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8010, help="Bind port (default 8010)")
    args = parser.parse_args()

    if not INDEX_HTML.exists():
        raise SystemExit(f"UI file missing: {INDEX_HTML}")

    print(f"[progress] Selection store: {store.state_path()}")
    print(f"[progress] Starting YTS movie selector at http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
