"""JSON-сессия на каждого user_id. В памяти бот состояние не держит."""

import json
from pathlib import Path

from config import SESSION_DIR

SESSION_DIR.mkdir(exist_ok=True)


def new_session() -> dict:
    return {
        "state": "MENU",
        "name": None,
        "subscribed": False,
        "screen_message_id": None,
        "screen_chat_id": None,
        "gold": 130,
        "base_hp": 12,
        "wave": 0,
        "towers": [],
    }


def session_path(user_id: int) -> Path:
    return SESSION_DIR / f"{user_id}.json"


def load_session(user_id: int) -> dict:
    path = session_path(user_id)
    if not path.exists():
        return new_session()
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return new_session()
    base = new_session()
    if isinstance(data, dict):
        base.update(data)
    return base


def save_session(user_id: int, data: dict) -> None:
    path = session_path(user_id)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def all_sessions() -> list[tuple[int, dict]]:
    rows = []
    for path in SESSION_DIR.glob("*.json"):
        if not path.stem.isdigit():
            continue
        user_id = int(path.stem)
        rows.append((user_id, load_session(user_id)))
    return rows
