"""Стартовый экран, полоса HUD и экраны победы и поражения."""

import os

import pygame

from constants import COLORS, WINDOW_HEIGHT, WINDOW_WIDTH


def load_font(size):
    """Системный шрифт с кириллицей. Стандартный шрифт Pygame её не рисует."""
    for path in (
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ):
        if os.path.exists(path):
            return pygame.font.Font(path, size)
    return pygame.font.SysFont("arial", size)


def load_fonts():
    return {
        "small": load_font(16),
        "body": load_font(20),
        "medium": load_font(28),
        "big": load_font(52),
    }


def _blit_lines(surface, font, lines, x, y, color, gap):
    for line in lines:
        image = font.render(line, True, color)
        surface.blit(image, (x, y))
        y += gap
    return y


def draw_menu(surface, fonts, tower_cost, player_name):
    surface.fill(COLORS["bg"])
    title = fonts["big"].render("БАШНИ И ЭНЕРГИЯ", True, COLORS["text"])
    subtitle = fonts["medium"].render("Вариант 23. Защита базы на сетке", True, COLORS["gold"])
    surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 78)))
    surface.blit(subtitle, subtitle.get_rect(center=(WINDOW_WIDTH // 2, 128)))

    left_title = fonts["medium"].render("ПРАВИЛА", True, COLORS["gold"])
    right_title = fonts["medium"].render("ЛЕГЕНДА", True, COLORS["gold"])
    surface.blit(left_title, (48, 180))
    surface.blit(right_title, (470, 180))
    left = [
        "Монстры идут по тропе к базе.",
        "Левая кнопка мыши ставит башню.",
        "Башня бьёт ближайшего врага.",
        "Выстрел — один раз в секунду.",
        "Без питания башня не стреляет.",
        "Питание идёт от генератора.",
    ]
    right = [
        "Жёлтый круг — генератор",
        "Синяя башня — есть питание",
        "Серая башня — нет питания",
        "Синяя линия — энергосеть",
        "Красный круг — монстр",
        "Зелёная клетка — база",
    ]
    _blit_lines(surface, fonts["body"], left, 48, 230, COLORS["text"], 36)
    _blit_lines(surface, fonts["body"], right, 470, 230, COLORS["text"], 36)

    name_text = f"Имя: {player_name}_" if player_name else "Имя: _"
    name_image = fonts["body"].render(name_text, True, COLORS["text"])
    surface.blit(name_image, name_image.get_rect(center=(WINDOW_WIDTH // 2, 480)))
    hint = fonts["medium"].render("Enter — начать игру", True, COLORS["gold"])
    surface.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, 520)))
    cost = fonts["small"].render(
        f"Башня стоит {tower_cost:g} золота. На тропе и на генераторе строить нельзя.",
        True,
        COLORS["muted"],
    )
    surface.blit(cost, cost.get_rect(center=(WINDOW_WIDTH // 2, 560)))


def draw_hud(surface, fonts, gold, base_hp, wave_label, notice):
    """Три подписи с полями по краям, чтобы они не наезжали друг на друга."""
    bar = pygame.Rect(0, 0, WINDOW_WIDTH, 40)
    pygame.draw.rect(surface, COLORS["hud"], bar)
    gold_image = fonts["small"].render(f"Золото: {gold}", True, COLORS["gold"])
    wave_image = fonts["small"].render(wave_label, True, COLORS["text"])
    base_image = fonts["small"].render(f"База: {base_hp}", True, COLORS["victory"])
    surface.blit(gold_image, (16, 11))
    surface.blit(wave_image, wave_image.get_rect(center=(WINDOW_WIDTH // 2, 20)))
    surface.blit(base_image, base_image.get_rect(midright=(WINDOW_WIDTH - 16, 20)))

    if notice:
        note = fonts["small"].render(notice, True, COLORS["warning"])
        plate = note.get_rect(center=(WINDOW_WIDTH // 2, 62)).inflate(16, 8)
        pygame.draw.rect(surface, COLORS["hud"], plate)
        surface.blit(note, note.get_rect(center=plate.center))


def draw_end_screen(surface, fonts, victory):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((*COLORS["overlay"], 210))
    surface.blit(overlay, (0, 0))

    if victory:
        title = fonts["big"].render("ВОЛНЫ ОТБИТЫ", True, COLORS["victory"])
        lines = ("База уцелела.", "Все волны пройдены.")
    else:
        title = fonts["big"].render("БАЗА РАЗРУШЕНА", True, COLORS["defeat"])
        lines = ("Монстры дошли до конца тропы.", "Здоровье базы закончилось.")

    surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 240)))
    y = 310
    for line in lines:
        body = fonts["body"].render(line, True, COLORS["text"])
        surface.blit(body, body.get_rect(center=(WINDOW_WIDTH // 2, y)))
        y += 32
    hint = fonts["medium"].render("Нажмите R, чтобы вернуться в меню", True, COLORS["gold"])
    surface.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, 390)))
