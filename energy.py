"""Энергосеть: башня стреляет, только если до неё дошло питание.

Связь есть, когда расстояние меньше D. Питание идёт от генератора
к соседним башням и дальше по цепочке. Это обход графа в ширину:
вершины — генератор и башни, ребро — пара ближе чем D.
"""

import math

from constants import ENERGY_DISTANCE


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def power_network(generator_xy, towers, max_distance=ENERGY_DISTANCE):
    """Помечает запитанные башни и возвращает линии, по которым пришло питание.

    Условие из задания строгое: расстояние должно быть меньше D, не равно ему.
    """
    for tower in towers:
        tower.powered = False

    links = []
    # В очереди лежат уже запитанные точки. Первая — сам генератор.
    queue = [generator_xy]
    head = 0

    while head < len(queue):
        source = queue[head]
        head += 1
        for tower in towers:
            if tower.powered:
                continue
            if distance(source, (tower.x, tower.y)) < max_distance:
                tower.powered = True
                links.append((source, (tower.x, tower.y)))
                queue.append((tower.x, tower.y))

    return links
