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


def _append_event(log_path: Path, event: dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")


def _source_metadata(source) -> dict:
    metadata = getattr(source, "last_run_metadata", {})
    return metadata if isinstance(metadata, dict) else {}


def run_shadow_check(
    source, state_path, log_path, now=None, duration_hours=48
) -> dict:
    now = now or datetime.now(timezone.utc)
    state_path = Path(state_path)
    log_path = Path(log_path)
    state = _load_state(state_path)
    started_at = parse_tibo_datetime(state.get("started_at") or now.isoformat())
    state.setdefault("started_at", started_at.isoformat())
    if now >= started_at + timedelta(hours=duration_hours):
        state.setdefault("completed_at", now.isoformat())
        _save_state(state_path, state)
        return {"status": "complete", "observed_ids": []}

    since_id = state.get("latest_post_id")
    last_checked_at = state.get("last_checked_at")
    since = (
        parse_tibo_datetime(last_checked_at) - timedelta(minutes=5)
        if last_checked_at
        else now - timedelta(hours=24)
    )

    try:
        posts = source.fetch_since_id(since_id, since, now)
    except Exception as exc:
        event = {
            "status": "error",
            "checked_at": now.isoformat(),
            "since_id": since_id,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
            "actor_run": _source_metadata(source),
        }
        _append_event(log_path, event)
        state["run_count"] = int(state.get("run_count", 0)) + 1
        state["error_count"] = int(state.get("error_count", 0)) + 1
        state["last_attempt_at"] = now.isoformat()
        _save_state(state_path, state)
        raise

    observed_ids = [post.post_id for post in posts]
    latest_post_id = _newest_post_id([since_id, *observed_ids])
    event = {
        "status": "success",
        "checked_at": now.isoformat(),
        "since_id": since_id,
        "observed_ids": observed_ids,
        "actor_run": _source_metadata(source),
        "posts": [
            {
                "post_id": post.post_id,
                "created_at": post.created_at.isoformat(),
                "url": post.url,
                "is_reply": post.is_reply,
                "is_quote": post.is_quote,
                "is_repost": post.is_repost,
                "kind": (
                    "repost"
                    if post.is_repost
                    else "reply"
                    if post.is_reply
                    else "quote"
                    if post.is_quote
                    else "original"
                ),
            }
            for post in posts
        ],
    }

    _append_event(log_path, event)

    state.update(
        {
            "latest_post_id": latest_post_id,
            "last_checked_at": now.isoformat(),
            "last_attempt_at": now.isoformat(),
            "run_count": int(state.get("run_count", 0)) + 1,
            "observed_ids": list(
                dict.fromkeys([*state.get("observed_ids", []), *observed_ids])
            )[-500:],
        }
    )
    _save_state(state_path, state)
    return event
