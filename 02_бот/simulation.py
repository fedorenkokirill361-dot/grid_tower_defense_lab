"""Текстовая симуляция штаба. Окно Pygame здесь не открывается.

Карта берётся из constants.py, волны и лазер — из defense_balances.json,
если файл читается. Башня стреляет только если поиск в ширину от генератора
дошёл до неё ближе чем ENERGY_DISTANCE.
"""

import importlib.util
import math
import sys

from config import GAME_DIR

TILE = 40


def _load_game():
    path = GAME_DIR / "constants.py"
    spec = importlib.util.spec_from_file_location("01_игра_constants", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.path.insert(1, str(GAME_DIR))
    import data_io

    return module, data_io.load_balances()


CONST, BALANCE = _load_game()

TOWER_TYPES = {
    "лазер": {
        "cost": BALANCE.tower_cost,
        "damage": BALANCE.tower_damage,
        "radius": BALANCE.attack_radius,
    },
    "пулемёт": {"cost": 25, "damage": 10, "radius": 80},
    "мортира": {"cost": 70, "damage": 35, "radius": 160},
}


def cell_center(col: int, row: int) -> tuple[float, float]:
    return col * TILE + TILE / 2, row * TILE + TILE / 2


def cells_on_segment(start, end) -> list[tuple[int, int]]:
    col1, row1 = start
    col2, row2 = end
    cells = []
    if col1 == col2:
        step = 1 if row2 >= row1 else -1
        for row in range(row1, row2 + step, step):
            cells.append((col1, row))
    elif row1 == row2:
        step = 1 if col2 >= col1 else -1
        for col in range(col1, col2 + step, step):
            cells.append((col, row1))
    return cells


def build_path_cells(corners) -> set[tuple[int, int]]:
    cells = []
    for start, end in zip(corners, corners[1:]):
        segment = cells_on_segment(start, end)
        if cells:
            segment = segment[1:]
        cells.extend(segment)
    return set(cells)


PATH_CELLS = build_path_cells(CONST.PATH_CORNERS)
GENERATOR = CONST.GENERATOR_CELL


def _distance(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def powered_towers(towers: list[dict]) -> list[dict]:
    """BFS: питание идёт от генератора к башне, если расстояние меньше D."""
    powered = []
    queue = [cell_center(*GENERATOR)]
    head = 0
    seen = set()
    while head < len(queue):
        source = queue[head]
        head += 1
        for index, tower in enumerate(towers):
            if index in seen:
                continue
            point = cell_center(tower["col"], tower["row"])
            if _distance(source, point) < CONST.ENERGY_DISTANCE:
                seen.add(index)
                powered.append(tower)
                queue.append(point)
    return powered


def _path_samples() -> list[tuple[float, float]]:
    samples = []
    corners = CONST.PATH_CORNERS
    for start, end in zip(corners, corners[1:]):
        ax, ay = cell_center(*start)
        bx, by = cell_center(*end)
        length = _distance((ax, ay), (bx, by))
        steps = max(1, int(length / 8))
        for step in range(steps):
            t = step / steps
            samples.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    samples.append(cell_center(*corners[-1]))
    return samples


PATH_SAMPLES = _path_samples()


def exposure_length(tower: dict) -> float:
    """Длина участка тропы, который попадает в радиус башни."""
    point = cell_center(tower["col"], tower["row"])
    radius = TOWER_TYPES[tower["type"]]["radius"]
    hits = 0
    for sample in PATH_SAMPLES:
        if _distance(point, sample) <= radius:
            hits += 1
    return hits * 8


def place_tower(session: dict, tower_type: str, col: int, row: int) -> str:
    kind = tower_type.lower()
    if kind not in TOWER_TYPES:
        names = ", ".join(TOWER_TYPES)
        return f"Неизвестный тип. Доступны: {names}."
    if not (0 <= col < CONST.GRID_COLUMNS and 0 <= row < CONST.GRID_ROWS):
        return "Клетка вне сетки 20 на 14."
    if (col, row) in PATH_CELLS or (col, row) == GENERATOR:
        return "На тропе и на генераторе строить нельзя."
    if any(item["col"] == col and item["row"] == row for item in session["towers"]):
        return "Эта клетка уже занята."
    cost = TOWER_TYPES[kind]["cost"]
    if session["gold"] < cost:
        return f"Не хватает золота: нужно {cost}, есть {session['gold']}."
    session["gold"] -= cost
    session["towers"].append({"type": kind, "col": col, "row": row})
    return f"Построена башня «{kind}» на клетке ({col}, {row}). Золото: {session['gold']}."


def resolve_next_wave(session: dict) -> str:
    """Один шаг волны по уже построенным башням. Меняет gold, base_hp и wave."""
    if session["base_hp"] <= 0:
        return "База уже разрушена. Новая волна не запускается."
    index = session["wave"]
    if index >= len(BALANCE.waves):
        return "Все волны из списка уже выпущены."
    wave = BALANCE.waves[index]
    session["wave"] = index + 1
    active = powered_towers(session["towers"])
    silent = len(session["towers"]) - len(active)
    total_damage = 0
    for tower in active:
        length = exposure_length(tower)
        if length <= 0:
            continue
        time_sec = length / wave["speed"]
        shots = max(1, int(time_sec / CONST.FIRE_INTERVAL))
        total_damage += shots * TOWER_TYPES[tower["type"]]["damage"]
    killed = min(wave["count"], int(total_damage // wave["hp"])) if wave["hp"] else 0
    leaked = wave["count"] - killed
    session["base_hp"] = max(0, session["base_hp"] - leaked)
    gained = killed * wave["reward"]
    session["gold"] += gained
    lines = [
        f"Волна {index + 1}. Монстров: {wave['count']}, здоровье каждого: {wave['hp']}.",
        f"Башен с питанием: {len(active)}. Без питания: {silent}.",
        f"Убито: {killed}. Прорвалось: {leaked}.",
        f"Золото: +{gained}, теперь {session['gold']}.",
        f"Здоровье базы: {session['base_hp']}.",
    ]
    if session["base_hp"] <= 0:
        lines.append("База разрушена.")
    return "\n".join(lines)


def status_text(session: dict) -> str:
    if not session["towers"]:
        built = "башен нет"
    else:
        built = ", ".join(
            f"{item['type']} ({item['col']}, {item['row']})" for item in session["towers"]
        )
    name = session.get("name") or "не указано"
    return (
        f"Имя: {name}\n"
        f"Золото: {session['gold']}\n"
        f"Здоровье базы: {session['base_hp']}\n"
        f"Пройдено волн: {session['wave']}\n"
        f"Башни: {built}"
    )
