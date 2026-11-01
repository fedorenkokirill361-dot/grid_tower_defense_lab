/** Башня бьёт ближайшую цель, если выстрел проходит порог формулы и кулдаун прошёл. */

import { FIRE_INTERVAL_MS, TOWER_STATE } from './constants.js';
import { Beam } from './beam.js';
import { distance, shotConnects } from './formulas.js';
import { Rect } from './rect.js';

export class Tower {
    constructor(col, row, spec, center) {
        this.col = col;
        this.row = row;
        this.name = spec.name;
        this.damage = spec.damage;
        this.radius = spec.radius;
        this.cost = spec.cost;
        this.energyType = spec.energyType;
        this.x = center[0];
        this.y = center[1];
        this.powered = false;
        this.state = TOWER_STATE.UNPOWERED;
        this.lastActionTime = -FIRE_INTERVAL_MS;
        this.forceShot = false;
        this.rect = new Rect(this.x - 11, this.y - 11, 22, 22);
    }

    nearest(enemies, attackScale = 1) {
        let chosen = null;
        let best = Infinity;
        for (const enemy of enemies) {
            if (!enemy.alive || enemy.finished) {
                continue;
            }
            const gap = distance(this.x, this.y, enemy.x, enemy.y);
            if (!shotConnects(gap, this.radius, attackScale) || gap > best) {
                continue;
            }
            chosen = enemy;
            best = gap;
        }
        return chosen;
    }

    /**
     * Один выстрел, если питание есть и с прошлого выстрела прошла секунда.
     * modifier умножает урон. Возвращает луч или null.
     */
    act(nowMs, enemies, modifier = 1, attackScale = 1) {
        if (!this.powered) {
            this.state = TOWER_STATE.UNPOWERED;
            return null;
        }
        const ready = this.forceShot || nowMs - this.lastActionTime >= FIRE_INTERVAL_MS;
        if (!ready) {
            this.state = TOWER_STATE.COOLDOWN;
            return null;
        }
        const target = this.nearest(enemies, attackScale);
        if (!target) {
            this.state = TOWER_STATE.IDLE;
            return null;
        }
        this.state = TOWER_STATE.AIM;
        target.takeDamage(this.damage * modifier);
        this.lastActionTime = nowMs;
        this.forceShot = false;
        this.state = TOWER_STATE.COOLDOWN;
        return new Beam(this.x, this.y, target.x, target.y);
    }
}
