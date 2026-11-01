"""Разбор scores.csv и log_defense.txt. Битая строка не роняет бота."""

import csv
import re
from dataclasses import dataclass

from config import DEFENSE_LOG_PATH, SCORES_PATH

STATUSES = {"Победа", "Поражение"}
TIME_RE = re.compile(r"^\d{2}:\d{2}:\d{2}$")


@dataclass
class Record:
    name: str
    wave: int
    status: str
    time_text: str


def verify_record(record: Record) -> list[str]:
    issues = []
    if not record.name:
        issues.append("пустое имя")
    if record.wave < 1 or record.wave > 99:
        issues.append("волна вне диапазона 1..99")
    if record.status not in STATUSES:
        issues.append("статус должен быть «Победа» или «Поражение»")
    if not TIME_RE.match(record.time_text):
        issues.append("время должно быть в формате HH:MM:SS")
    return issues


def parse_scores_text(text: str) -> tuple[list[Record], list[str]]:
    records = []
    errors = []
    rows = list(csv.reader(text.splitlines()))
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    if not rows:
        return records, ["файл пуст"]
    start = 1 if rows[0] and rows[0][0].strip().lower() in {"имя", "name"} else 0
    for line_no, row in enumerate(rows[start:], start=start + 1):
        if len(row) != 4:
            errors.append(f"Строка {line_no}: ожидается 4 поля")
            continue
        name, wave_text, status, time_text = (cell.strip() for cell in row)
        try:
            record = Record(name, int(wave_text), status, time_text)
        except ValueError:
            errors.append(f"Строка {line_no}: волна не число")
            continue
        issues = verify_record(record)
        if issues:
            errors.append(f"Строка {line_no}: {', '.join(issues)}")
            continue
        records.append(record)
    return records, errors


def read_scores(path=SCORES_PATH) -> tuple[list[Record], list[str]]:
    if not path.exists():
        return [], ["файл результатов не найден"]
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as error:
        return [], [f"не удалось прочитать файл: {error}"]
    return parse_scores_text(text)


def append_records(records: list[Record], path=SCORES_PATH) -> int:
    new_file = not path.exists() or path.stat().st_size == 0
    with open(path, "a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        if new_file:
            writer.writerow(["Имя", "Волна", "Статус", "Время"])
        for record in records:
            writer.writerow([record.name, record.wave, record.status, record.time_text])
    return len(records)


def leaderboard(records: list[Record], limit: int = 10) -> list[Record]:
    def key(record: Record):
        win = 0 if record.status == "Победа" else 1
        return (win, -record.wave, record.name)

    return sorted(records, key=key)[:limit]


def format_leaderboard(records: list[Record]) -> str:
    rows = leaderboard(records)
    if not rows:
        return "Результатов пока нет."
    lines = ["#  Имя                Волна  Статус"]
    for index, record in enumerate(rows, start=1):
        lines.append(f"{index:<2} {record.name[:18]:<18} {record.wave:>5}  {record.status}")
    return "\n".join(lines)


def personal_stats(records: list[Record], name: str) -> str:
    own = [record for record in records if record.name == name]
    if not own:
        return f"Для имени «{name}» записей нет."
    wins = sum(record.status == "Победа" for record in own)
    best = max(record.wave for record in own)
    return f"Имя: {name}\nПартий: {len(own)}\nПобед: {wins}\nЛучшая волна: {best}"


def achievements(records: list[Record], name: str) -> list[str]:
    own = [record for record in records if record.name == name]
    result = []
    if own:
        result.append("Штаб: есть хотя бы одна запись в таблице.")
    if any(record.status == "Победа" for record in own):
        result.append("Удержание: есть победа.")
    if any(record.wave >= 5 for record in own):
        result.append("Пятая волна: партия дошла до волны 5 или дальше.")
    return result or ["Достижений пока нет."]


def read_defense_log(path=DEFENSE_LOG_PATH, limit: int = 5) -> str:
    if not path.exists():
        return "Лог поражений игры пуст."
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return f"Лог не прочитан: {error}"
    lines = [line for line in lines if line.strip()]
    if not lines:
        return "Лог поражений игры пуст."
    tail = lines[-limit:]
    return "Последние поражения из игры:\n" + "\n".join(tail)
