"""Монстр, который идёт по опорным точкам тропинки."""

import math

import pygame

from constants import COLORS


class Enemy:
    """Один монстр волны.

    Позиция меняется плавно: каждый кадр монстр сдвигается к текущей
    опорной точке на speed * dt. Когда точка достигнута, целью становится
    следующая. После последней точки монстр дошёл до базы.
    """

    def __init__(self, waypoints, hp, speed, reward):
        self.waypoints = waypoints
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.reward = reward
        self.x, self.y = waypoints[0]
        # Индекс точки, к которой монстр сейчас идёт. На старте он уже
        # стоит в первой точке, поэтому цель — вторая.
        self.waypoint_index = 1
        self.alive = True
        self.finished = False

    def update(self, dt):
        if not self.alive or self.finished:
            return
        if self.waypoint_index >= len(self.waypoints):
            self.finished = True
            return

        target_x, target_y = self.waypoints[self.waypoint_index]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)
        step = self.speed * dt

        if distance <= step:
            self.x = target_x
            self.y = target_y
            self.waypoint_index += 1
            if self.waypoint_index >= len(self.waypoints):
                self.finished = True
        else:
            self.x += dx / distance * step
            self.y += dy / distance * step

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive or self.finished:
            return
        pygame.draw.circle(surface, COLORS["enemy"], (int(self.x), int(self.y)), 12)
        bar_width = 22
        bar_x = int(self.x - bar_width / 2)
        bar_y = int(self.y - 20)
        pygame.draw.rect(surface, COLORS["enemy_hp_back"], (bar_x, bar_y, bar_width, 4))
        ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(
            surface,
            COLORS["enemy_hp"],
            (bar_x, bar_y, int(bar_width * ratio), 4),
        )
