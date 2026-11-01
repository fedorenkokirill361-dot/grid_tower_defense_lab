/** Расстояние и пороги. Голый «d <= R» из ЛР 1 здесь заменён значением формулы. */

import {
    ATTACK_DECAY,
    ATTACK_P0,
    ATTACK_RADIUS,
    ENERGY_DECAY,
    ENERGY_P0,
    ENERGY_THRESHOLD,
    HIT_THRESHOLD,
} from './constants.js';

export function distance(x1, y1, x2, y2) {
    return Math.hypot(x2 - x1, y2 - y1);
}

/** Сила питания на расстоянии d: P(d) = P0 * exp(-k * scale * d). */
export function energyAt(d, scale = 1) {
    return ENERGY_P0 * Math.exp(-ENERGY_DECAY * scale * d);
}

/** Расстояние, на котором питание ещё выше порога. При scale = 2 оно вдвое меньше. */
export function energyLimit(scale = 1) {
    return Math.log(ENERGY_P0 / ENERGY_THRESHOLD) / (ENERGY_DECAY * scale);
}

/** Связь есть, только если расчётное питание строго выше порога. На границе D связи нет. */
export function energyLinkOk(d, scale = 1) {
    return energyAt(d, scale) > ENERGY_THRESHOLD;
}

/** Сила попадания. k считается от радиуса башни, чтобы порог лежал на окружности R. */
export function attackAt(d, radius = ATTACK_RADIUS, scale = 1) {
    const decay = (Math.log(ATTACK_P0 / HIT_THRESHOLD) / radius) * scale;
    return ATTACK_P0 * Math.exp(-decay * d);
}

export function attackLimit(radius = ATTACK_RADIUS, scale = 1) {
    return radius / scale;
}

/** Выстрел засчитан, если сила на дистанции не ниже порога и цель не дальше предела формулы. */
export function shotConnects(d, radius = ATTACK_RADIUS, scale = 1) {
    return attackAt(d, radius, scale) + 1e-8 >= HIT_THRESHOLD && d <= attackLimit(radius, scale) + 1e-6;
}

export { ATTACK_DECAY, ENERGY_DECAY };
