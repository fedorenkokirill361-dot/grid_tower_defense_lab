/** Параметры варианта 23. Имена совпадают с константами Python-игры. */

export const TILE_SIZE = 40;
export const GRID_COLUMNS = 20;
export const GRID_ROWS = 14;
export const FIELD_WIDTH = GRID_COLUMNS * TILE_SIZE;
export const FIELD_HEIGHT = GRID_ROWS * TILE_SIZE;

export const ATTACK_RADIUS = 120;
export const ENERGY_DISTANCE = 150;
export const FIRE_INTERVAL_MS = 1000;
export const TOWER_DAMAGE = 18;
export const TOWER_COST = 40;
export const START_GOLD = 130;
export const BASE_HP = 12;

export const FIRST_WAVE_DELAY_MS = 5000;
export const WAVE_PAUSE_MS = 6000;
export const SPAWN_INTERVAL_MS = 850;
export const STAGGER_MS = 350;

/** База формулы: у источника значение 1, порог — доля, ниже которой эффекта нет. */
export const ENERGY_P0 = 1;
export const ENERGY_THRESHOLD = 0.15;
export const ATTACK_P0 = 1;
export const HIT_THRESHOLD = 0.15;

/**
 * Коэффициент затухания подобран так, чтобы порог приходился на D из ЛР 1.
 * k = ln(P0 / порог) / D. Удвоение k сдвигает порог вдвое ближе.
 */
export const ENERGY_DECAY = Math.log(ENERGY_P0 / ENERGY_THRESHOLD) / ENERGY_DISTANCE;
export const ATTACK_DECAY = Math.log(ATTACK_P0 / HIT_THRESHOLD) / ATTACK_RADIUS;

export const PATH_CORNERS = [
    [0, 1],
    [4, 1],
    [4, 5],
    [10, 5],
    [10, 2],
    [15, 2],
    [15, 11],
    [19, 11],
];

export const GENERATOR_CELL = [7, 9];

export const WAVES = [
    { count: 6, hp: 36, speed: 55, reward: 8 },
    { count: 8, hp: 54, speed: 62, reward: 9 },
    { count: 10, hp: 72, speed: 68, reward: 10 },
    { count: 8, hp: 120, speed: 52, reward: 15 },
    { count: 12, hp: 96, speed: 78, reward: 12 },
];

/** Марш прерывается попаданием, затем монстр возвращается к той же опорной точке. */
export const ENEMY_STATE = Object.freeze({
    MARCH: 'March',
    STAGGER: 'Stagger',
    RETURN: 'Return',
    DEAD: 'Dead',
    LEAKED: 'Leaked',
});

/** Башня без питания молчит. После выстрела кулдаун возвращает её в ожидание. */
export const TOWER_STATE = Object.freeze({
    UNPOWERED: 'Unpowered',
    IDLE: 'Idle',
    AIM: 'Aim',
    COOLDOWN: 'Cooldown',
});

export const STATE_PLAY = 'play';
export const STATE_VICTORY = 'victory';
export const STATE_DEFEAT = 'defeat';
