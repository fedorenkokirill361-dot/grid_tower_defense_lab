"""Башня: выбор цели по расстоянию и выстрел раз в секунду."""

import math

import pygame

from constants import COLORS, FIRE_INTERVAL
from level import cell_center


class Tower:
    """Оборонительная башня на одной клетке сетки.

    Стреляет только если энергосеть отметила башню как запитанную.
    Цель — ближайший живой монстр, расстояние до которого не больше R.
    """

    def __init__(self, col, row, damage, radius):
        self.col = col
        self.row = row
        self.x, self.y = cell_center(col, row)
        self.damage = damage
        self.radius = radius
        self.cooldown = 0.0
        self.powered = False
        self.beam_time = 0.0
        self.beam_target = None

    def nearest_enemy(self, enemies):
        """Ближайший монстр в радиусе атаки или None, если таких нет."""
        chosen = None
        best_distance = self.radius
        for enemy in enemies:
            if not enemy.alive or enemy.finished:
                continue
            distance = math.hypot(enemy.x - self.x, enemy.y - self.y)
            # «В радиусе R» включает границу окружности.
            if distance <= best_distance:
                chosen = enemy
                best_distance = distance
        return chosen

    def update(self, dt, enemies):
        self.cooldown = max(0.0, self.cooldown - dt)
        self.beam_time = max(0.0, self.beam_time - dt)

        if not self.powered:
            return

        target = self.nearest_enemy(enemies)
        if target is None or self.cooldown > 0:
            return

        target.take_damage(self.damage)
        self.cooldown = FIRE_INTERVAL
        self.beam_time = 0.12
        self.beam_target = (target.x, target.y)

    def draw(self, surface, show_range):
        color = COLORS["tower_on"] if self.powered else COLORS["tower_off"]
        rect = pygame.Rect(0, 0, 22, 22)
        rect.center = (int(self.x), int(self.y))
        pygame.draw.rect(surface, color, rect)
        if self.powered:
            pygame.draw.circle(surface, COLORS["generator_core"], (int(self.x), int(self.y)), 4)

        if show_range:
            diameter = int(self.radius * 2)
            range_surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(
                range_surface,
                (*COLORS["range"], 50),
                (int(self.radius), int(self.radius)),
                int(self.radius),
                1,
            )
            surface.blit(range_surface, (self.x - self.radius, self.y - self.radius))

        if self.beam_time > 0 and self.beam_target is not None:
            pygame.draw.line(
                surface,
                COLORS["laser"],
                (int(self.x), int(self.y)),
                (int(self.beam_target[0]), int(self.beam_target[1])),
                2,
            )
