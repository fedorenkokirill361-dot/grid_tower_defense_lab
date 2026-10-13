"""Сетка, тропинка и статичные объекты поля.

Тропа задаётся списком опорных точек. Между соседними точками
монстр идёт по прямой, а клетки этого отрезка нельзя застраивать.
"""

import pygame

from constants import (
    COLORS,
    GENERATOR_CELL,
    GRID_COLUMNS,
    GRID_ROWS,
    HUD_HEIGHT,
    PATH_CORNERS,
    TILE_SIZE,
)


def cell_center(col, row):
    """Пиксельный центр клетки. По ним движутся монстры и стоят башни."""
    x = col * TILE_SIZE + TILE_SIZE // 2
    y = HUD_HEIGHT + row * TILE_SIZE + TILE_SIZE // 2
    return x, y


def cell_from_pixel(px, py):
    """Переводит клик мыши в клетку сетки. None, если клик вне поля."""
    if py < HUD_HEIGHT:
        return None
    col = px // TILE_SIZE
    row = (py - HUD_HEIGHT) // TILE_SIZE
    if 0 <= col < GRID_COLUMNS and 0 <= row < GRID_ROWS:
        return col, row
    return None


def cell_rect(col, row):
    return pygame.Rect(
        col * TILE_SIZE,
        HUD_HEIGHT + row * TILE_SIZE,
        TILE_SIZE,
        TILE_SIZE,
    )


def cells_on_segment(start, end):
    """Клетки прямого отрезка между двумя опорными точками.

    Отрезок только горизонтальный или вертикальный: так тропа
    совпадает с сеткой, по которой ставятся башни.
    """
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
    else:
        raise ValueError("Опорные точки тропы должны стоять на одной прямой")
    return cells


def build_path_cells(corners):
    """Все клетки тропы без повтора стыка соседних отрезков."""
    cells = []
    for start, end in zip(corners, corners[1:]):
        segment = cells_on_segment(start, end)
        if cells:
            segment = segment[1:]
        cells.extend(segment)
    return cells


PATH_CELLS = set(build_path_cells(PATH_CORNERS))
WAYPOINTS = [cell_center(col, row) for col, row in PATH_CORNERS]
BASE_CELL = PATH_CORNERS[-1]


def is_buildable_cell(col, row):
    """На тропе и на клетке генератора башню ставить нельзя."""
    return (col, row) not in PATH_CELLS and (col, row) != GENERATOR_CELL


def draw_level(surface, font):
    """Рисует сетку, тропу, генератор и базу."""
    surface.fill(COLORS["bg"])

    for row in range(GRID_ROWS):
        for col in range(GRID_COLUMNS):
            rect = cell_rect(col, row)
            if (col, row) in PATH_CELLS:
                pygame.draw.rect(surface, COLORS["path"], rect)
            pygame.draw.rect(surface, COLORS["grid"], rect, 1)

    if len(WAYPOINTS) >= 2:
        pygame.draw.lines(surface, COLORS["path_line"], False, WAYPOINTS, 4)
    for point in WAYPOINTS:
        pygame.draw.circle(surface, COLORS["waypoint"], point, 4)

    generator = cell_center(*GENERATOR_CELL)
    pygame.draw.circle(surface, COLORS["generator"], generator, 16)
    pygame.draw.circle(surface, COLORS["generator_core"], generator, 7)

    base_rect = cell_rect(*BASE_CELL)
    pygame.draw.rect(surface, COLORS["base"], base_rect.inflate(-6, -6))
    label = font.render("БАЗА", True, COLORS["text"])
    # Клетка у края окна узкая: длинная подпись обрезалась бы по границе.
    max_width = TILE_SIZE - 10
    if label.get_width() > max_width:
        scale = max_width / label.get_width()
        label = pygame.transform.smoothscale(
            label,
            (max_width, max(1, int(label.get_height() * scale))),
        )
    surface.blit(label, label.get_rect(center=base_rect.center))
