"""Пути, токен и параметры бота. Токен читается из .env, не из кода."""

import os
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parent
ROOT_DIR = BOT_DIR.parent
# Локально игра лежит в 01_игра. В коммитах лаб 1–2 те же файлы ещё в корне репозитория.
_game_dir = ROOT_DIR / "01_игра"
GAME_DIR = _game_dir if _game_dir.exists() else ROOT_DIR
SESSION_DIR = BOT_DIR / "sessions"
SCORES_PATH = GAME_DIR / "scores.csv"
DEFENSE_LOG_PATH = GAME_DIR / "log_defense.txt"
BOT_LOG_PATH = BOT_DIR / "bot_flight.log"
ENV_PATH = BOT_DIR / ".env"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv(ENV_PATH)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WAVE_INTERVAL_SECONDS = int(os.environ.get("WAVE_INTERVAL_SECONDS", "3600"))

_admin_raw = os.environ.get("ADMIN_IDS", "")
ADMIN_IDS = set()
for item in _admin_raw.replace(" ", "").split(","):
    if item.isdigit():
        ADMIN_IDS.add(int(item))
