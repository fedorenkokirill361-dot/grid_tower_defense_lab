"""Игровой цикл: ввод, обновление состояния и отрисовка."""

import math

import pygame

from constants import (
    BASE_HP,
    COLORS,
    ENERGY_DISTANCE,
    FIRST_WAVE_DELAY,
    FPS,
    GENERATOR_CELL,
    SPAWN_INTERVAL,
    START_GOLD,
    STATE_DEFEAT,
    STATE_MENU,
    STATE_PLAY,
    STATE_VICTORY,
    WAVE_PAUSE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from data_io import load_balances, log_defeat
from enemy import Enemy
from energy import power_network
from level import (
    WAYPOINTS,
    cell_center,
    cell_from_pixel,
    draw_level,
    is_buildable_cell,
)
from tower import Tower
from ui import draw_end_screen, draw_hud, draw_menu, load_fonts


class Game:
    """Состояния: меню, бой, победа, поражение."""

    def __init__(self):
        self.fonts = load_fonts()
        self.balance = load_balances()
        self.reset()

    def reset(self):
        self.state = STATE_MENU
        self.gold = START_GOLD
        self.base_hp = BASE_HP
        self.towers = []
        self.enemies = []
        self.links = []
        self.current_wave = 0
        self.spawned_in_wave = 0
        self.spawn_timer = FIRST_WAVE_DELAY
        self.last_started_wave = 0
        self.notice = ""
        self.notice_timer = 0.0
        self.hover_cell = None

    def start_play(self):
        self.reset()
        self.state = STATE_PLAY

    def notify(self, text):
        self.notice = text
        self.notice_timer = 1.6

    def wave_label(self):
        total = len(self.balance.waves)
        if self.current_wave >= total:
            return "Последняя волна"
        number = self.current_wave + 1
        if self.spawned_in_wave == 0:
            seconds = max(0, math.ceil(self.spawn_timer))
            return f"Волна {number} из {total}, через {seconds} сек."
        return f"Волна {number} из {total}"

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self._on_key(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._on_click(event.pos)
        elif event.type == pygame.MOUSEMOTION and self.state == STATE_PLAY:
            self.hover_cell = cell_from_pixel(*event.pos)

    def _on_key(self, key):
        # В меню любая клавиша начинает игру. R работает только на финальном экране,
        # чтобы случайный перезапуск не стирал расставленные башни.
        if self.state == STATE_MENU:
            self.start_play()
        elif self.state in (STATE_VICTORY, STATE_DEFEAT) and key == pygame.K_r:
            self.reset()

    def _on_click(self, pos):
        if self.state == STATE_MENU:
            self.start_play()
            return
        if self.state != STATE_PLAY:
            return
        self.try_build(pos)

    def try_build(self, pos):
        cell = cell_from_pixel(*pos)
        if cell is None:
            return
        col, row = cell
        if not is_buildable_cell(col, row):
            self.notify("На этой клетке строить нельзя")
            return
        if any(tower.col == col and tower.row == row for tower in self.towers):
            self.notify("Эта клетка уже занята")
            return
        if self.gold < self.balance.tower_cost:
            self.notify("Не хватает золота")
            return
        self.gold -= self.balance.tower_cost
        self.towers.append(
            Tower(col, row, self.balance.tower_damage, self.balance.attack_radius)
        )

    def update(self, dt):
        if self.notice_timer > 0:
            self.notice_timer -= dt
            if self.notice_timer <= 0:
                self.notice = ""

        if self.state != STATE_PLAY:
            return

        self._spawn(dt)
        for enemy in self.enemies:
            enemy.update(dt)

        # Сеть пересчитывается каждый кадр: новая башня сразу получает
        # или не получает питание от генератора и уже запитанных башен.
        generator = cell_center(*GENERATOR_CELL)
        self.links = power_network(generator, self.towers, ENERGY_DISTANCE)

        for tower in self.towers:
            tower.update(dt, self.enemies)

        self._resolve_enemies()
        self._check_outcome()

    def _spawn(self, dt):
        if self.current_wave >= len(self.balance.waves):
            return
        self.spawn_timer -= dt
        if self.spawn_timer > 0:
            return

        spec = self.balance.waves[self.current_wave]
        self.enemies.append(
            Enemy(WAYPOINTS, spec["hp"], spec["speed"], spec["reward"])
        )
        self.last_started_wave = self.current_wave + 1
        self.spawned_in_wave += 1
        if self.spawned_in_wave >= spec["count"]:
            self.current_wave += 1
            self.spawned_in_wave = 0
            self.spawn_timer = WAVE_PAUSE
        else:
            self.spawn_timer = SPAWN_INTERVAL

    def _resolve_enemies(self):
        kept = []
        for enemy in self.enemies:
            if enemy.hp <= 0 or not enemy.alive:
                self.gold += enemy.reward
                continue
            if enemy.finished:
                self.base_hp -= 1
                continue
            kept.append(enemy)
        self.enemies = kept

    def _check_outcome(self):
        if self.base_hp <= 0:
            self.base_hp = 0
            self.state = STATE_DEFEAT
            log_defeat(self.last_started_wave, self.towers)
            return
        waves_done = self.current_wave >= len(self.balance.waves)
        if waves_done and not self.enemies:
            self.state = STATE_VICTORY

    def draw(self, surface):
        # match сравнивает состояние с готовыми строками. Так экран
        # меню, боя и финала не смешиваются в одной цепочке if.
        match self.state:
            case "menu":
                draw_menu(surface, self.fonts, self.balance.tower_cost)
            case "play" | "victory" | "defeat":
                self._draw_battle(surface)
                if self.state == STATE_VICTORY:
                    draw_end_screen(surface, self.fonts, victory=True)
                elif self.state == STATE_DEFEAT:
                    draw_end_screen(surface, self.fonts, victory=False)

    def _draw_battle(self, surface):
        draw_level(surface, self.fonts["small"])
        for start, end in self.links:
            pygame.draw.line(surface, COLORS["energy"], start, end, 2)

        hover_tower = False
        for tower in self.towers:
            hovered = self.hover_cell == (tower.col, tower.row)
            hover_tower = hover_tower or hovered
            tower.draw(surface, show_range=hovered)

        if (
            self.hover_cell is not None
            and not hover_tower
            and is_buildable_cell(*self.hover_cell)
            and not any(
                (tower.col, tower.row) == self.hover_cell for tower in self.towers
            )
        ):
            preview = cell_center(*self.hover_cell)
            radius = int(self.balance.attack_radius)
            ghost = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                ghost,
                (*COLORS["tower_preview"], 40),
                (radius, radius),
                radius,
                1,
            )
            surface.blit(ghost, (preview[0] - radius, preview[1] - radius))
            rect = pygame.Rect(0, 0, 22, 22)
            rect.center = preview
            pygame.draw.rect(surface, COLORS["tower_preview"], rect, 2)

        for enemy in self.enemies:
            enemy.draw(surface)

        notice = self.notice if self.notice_timer > 0 else ""
        draw_hud(
            surface,
            self.fonts,
            self.gold,
            self.base_hp,
            self.wave_label(),
            notice,
        )


def run():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Башни и энергия — ЛР 1")
    clock = pygame.time.Clock()
    game = Game()

    while True:
        dt = clock.tick(FPS) / 1000
        # Если кадр задержался, монстр не должен перескочить всю тропу.
        dt = min(dt, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            game.handle_event(event)
        game.update(dt)
        game.draw(screen)
        pygame.display.flip()
