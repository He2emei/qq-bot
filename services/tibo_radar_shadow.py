import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

from services.tibo_radar_service import parse_tibo_datetime


def _load_state(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False
        ) as file:
            temporary_path = Path(file.name)
            json.dump(state, file, ensure_ascii=False, indent=2)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _newest_post_id(post_ids):
    valid_ids = [str(post_id) for post_id in post_ids if str(post_id).isdigit()]
    return max(valid_ids, key=int) if valid_ids else None


def run_shadow_check(source, state_path, log_path, now=None) -> dict:
    now = now or datetime.now(timezone.utc)
    state_path = Path(state_path)
    log_path = Path(log_path)
    state = _load_state(state_path)
    since_id = state.get("latest_post_id")
    last_checked_at = state.get("last_checked_at")
    since = (
        parse_tibo_datetime(last_checked_at) - timedelta(minutes=5)
        if last_checked_at
        else now - timedelta(hours=24)
    )

    posts = source.fetch_since_id(since_id, since, now)
    observed_ids = [post.post_id for post in posts]
    latest_post_id = _newest_post_id([since_id, *observed_ids])
    event = {
        "checked_at": now.isoformat(),
        "since_id": since_id,
        "observed_ids": observed_ids,
        "posts": [
            {
                "post_id": post.post_id,
                "created_at": post.created_at.isoformat(),
                "url": post.url,
                "is_reply": post.is_reply,
            }
            for post in posts
        ],
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")

    state.update(
        {
            "latest_post_id": latest_post_id,
            "last_checked_at": now.isoformat(),
            "run_count": int(state.get("run_count", 0)) + 1,
            "observed_ids": list(
                dict.fromkeys([*state.get("observed_ids", []), *observed_ids])
            )[-500:],
        }
    )
    _save_state(state_path, state)
    return event
