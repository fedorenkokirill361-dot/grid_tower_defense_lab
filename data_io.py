"""Чтение баланса из JSON, запись поражения в лог и строки в scores.csv.

Если defense_balances.json нет или он сломан, игра не закрывается:
берутся числа из constants.py, а причина печатается в консоль.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path

from constants import ATTACK_RADIUS, TOWER_COST, TOWER_DAMAGE, WAVES

FOLDER = Path(__file__).resolve().parent
BALANCES_PATH = FOLDER / "defense_balances.json"
DEFEAT_LOG_PATH = FOLDER / "log_defense.txt"
SCORES_PATH = FOLDER / "scores.csv"


class Balance:
    """Цифры, которыми партия пользуется после загрузки файла."""

    def __init__(self, tower_cost, tower_damage, attack_radius, waves):
        self.tower_cost = tower_cost
        self.tower_damage = tower_damage
        self.attack_radius = attack_radius
        self.waves = waves


def default_balance():
    """Запасной баланс, если JSON прочитать нельзя."""
    return Balance(TOWER_COST, TOWER_DAMAGE, ATTACK_RADIUS, list(WAVES))


def _as_number(value, name):
    """JSON мог подсунуть строку или пустое значение. Для баланса нужно число."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Поле {name} должно быть числом")
    return value


def parse_balances(data):
    """Достаёт из словаря цену, урон и радиус башни и список волн монстров."""
    if not isinstance(data, dict):
        raise ValueError("Корень JSON должен быть объектом")

    tower = data["tower"]
    monsters = data["monsters"]
    if not isinstance(tower, dict) or not isinstance(monsters, list) or not monsters:
        raise ValueError("В файле нет башни или списка монстров")

    waves = []
    for index, monster in enumerate(monsters, start=1):
        if not isinstance(monster, dict):
            raise ValueError(f"Волна {index} записана не объектом")
        waves.append(
            {
                "count": int(_as_number(monster["count"], "count")),
                "hp": _as_number(monster["hp"], "hp"),
                "speed": _as_number(monster["speed"], "speed"),
                "reward": _as_number(monster["reward"], "reward"),
            }
        )

    return Balance(
        tower_cost=_as_number(tower["cost"], "cost"),
        tower_damage=_as_number(tower["damage"], "damage"),
        attack_radius=_as_number(tower["radius"], "radius"),
        waves=waves,
    )


def load_balances(path=BALANCES_PATH):
    """Читает defense_balances.json. При ошибке возвращает запасные числа."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        balance = parse_balances(data)
    except FileNotFoundError:
        print(f"Файл {path.name} не найден. Используются числа из constants.py.")
        balance = default_balance()
    except json.JSONDecodeError:
        print(f"Файл {path.name} повреждён. Используются числа из constants.py.")
        balance = default_balance()
    except (KeyError, TypeError, ValueError) as error:
        print(f"В {path.name} не хватает полей ({error}). Используются числа из constants.py.")
        balance = default_balance()
    else:
        print(f"Баланс загружен из {path.name}.")
    return balance


def _defeat_logger():
    """Один логгер на файл log_defense.txt. Повторный вызов не плодит записи дважды."""
    logger = logging.getLogger("defense")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = logging.FileHandler(DEFEAT_LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)
    return logger


def save_score(name, wave, status, path=SCORES_PATH):
    """Дописывает результат партии в scores.csv.

    Если файла ещё нет, первая строка — заголовок.
    Время берётся в момент записи, формат HH:MM:SS.
    """
    new_file = not Path(path).exists()
    with open(path, "a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        if new_file:
            writer.writerow(["Имя", "Волна", "Статус", "Время"])
        writer.writerow([name, wave, status, datetime.now().strftime("%H:%M:%S")])


def log_defeat(wave_number, towers):
    """Пишет поражение: номер волны и координаты каждой поставленной башни."""
    if towers:
        places = []
        for tower in towers:
            places.append(
                f"клетка ({tower.col}, {tower.row}), пиксели ({int(tower.x)}, {int(tower.y)})"
            )
        tower_text = "; ".join(places)
    else:
        tower_text = "башен нет"
    _defeat_logger().info("Поражение. Финальная волна: %s. Башни: %s", wave_number, tower_text)
