"""
Selection store for the YTS movie selector web app.

Persisted JSON file (default: temp/yts_movie_selector/selection.json) that
tracks which movies the user selected in the web UI, so download_selected.py
can read the list and add the torrents to qBittorrent.
"""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STATE_PATH = WORKSPACE_ROOT / "temp" / "yts_movie_selector" / "selection.json"

VALID_STATUSES = {"pending", "downloaded"}

_lock = threading.Lock()


def state_path() -> Path:
    """State file location (YTS_SELECTION_PATH overrides the default)."""
    env = os.environ.get("YTS_SELECTION_PATH", "").strip()
    return Path(env) if env else DEFAULT_STATE_PATH


def _empty_state() -> dict:
    return {"version": 1, "selected": []}


def load_state() -> dict:
    path = state_path()
    if not path.exists():
        return _empty_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty_state()
    if not isinstance(data, dict) or not isinstance(data.get("selected"), list):
        return _empty_state()
    return data


def save_state(state: dict) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def list_selections(status: str | None = None) -> list:
    with _lock:
        items = load_state()["selected"]
    if status:
        items = [i for i in items if i.get("status") == status]
    return items


def get_selection(movie_id: int) -> dict | None:
    with _lock:
        items = load_state()["selected"]
    for item in items:
        if item.get("id") == movie_id:
            return item
    return None


def add_selection(movie: dict, status: str = "pending") -> dict:
    """Add (or refresh) a movie in the selection list, keyed by YTS movie id."""
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    movie_id = int(movie["id"])
    torrents = movie.get("torrents") or []
    item = {
        "id": movie_id,
        "imdb_code": movie.get("imdb_code"),
        "title": movie.get("title") or f"Movie {movie_id}",
        "year": movie.get("year"),
        "rating": movie.get("rating"),
        "poster": movie.get("cover") or movie.get("poster"),
        "quality": movie.get("quality"),
        "torrents": torrents,
        "status": status,
        "selected_at": _now(),
    }
    with _lock:
        state = load_state()
        selected = state["selected"]
        for i, existing in enumerate(selected):
            if existing.get("id") == movie_id:
                # keep original selected_at, refresh everything else
                item["selected_at"] = existing.get("selected_at", item["selected_at"])
                selected[i] = item
                break
        else:
            selected.append(item)
        save_state(state)
    return item


def remove_selection(movie_id: int) -> bool:
    with _lock:
        state = load_state()
        before = len(state["selected"])
        state["selected"] = [i for i in state["selected"] if i.get("id") != movie_id]
        removed = len(state["selected"]) < before
        if removed:
            save_state(state)
    return removed


def clear_selections() -> int:
    with _lock:
        state = load_state()
        removed = len(state["selected"])
        state["selected"] = []
        save_state(state)
    return removed


def set_status(movie_id: int, status: str) -> dict | None:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    with _lock:
        state = load_state()
        for item in state["selected"]:
            if item.get("id") == movie_id:
                item["status"] = status
                save_state(state)
                return item
    return None


if __name__ == "__main__":
    print(f"[progress] Selection store: {state_path()}")
    items = list_selections()
    print(f"[progress] {len(items)} selected movie(s)")
    for item in items:
        status = item.get("status", "?")
        qualities = ", ".join(t.get("quality", "?") for t in item.get("torrents", []))
        print(f"  - {item.get('title')} ({item.get('year')}) [{status}] {qualities}")
