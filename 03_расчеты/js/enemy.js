/** Монстр идёт по опорным точкам. Попадание прерывает шаг и запоминает точку возврата. */

import { ENEMY_STATE, STAGGER_MS } from './constants.js';
import { distance } from './formulas.js';

export class Enemy {
    constructor(waypoints, hp, speed, reward) {
        this.waypoints = waypoints;
        this.hp = hp;
        this.maxHp = hp;
        this.speed = speed;
        this.reward = reward;
        this.x = waypoints[0][0];
        this.y = waypoints[0][1];
        this.waypointIndex = 1;
        this.returnIndex = 1;
        this.state = ENEMY_STATE.MARCH;
        this.staggerMs = 0;
        this.alive = true;
        this.finished = false;
        this.ageMs = 0;
        this.stuckSteps = 0;
    }

    takeDamage(amount) {
        if (!this.alive || this.finished) {
            return;
        }
        this.hp -= amount;
        if (this.hp <= 0) {
            this.hp = 0;
            this.alive = false;
            this.state = ENEMY_STATE.DEAD;
            return;
        }
        if (this.state === ENEMY_STATE.MARCH || this.state === ENEMY_STATE.RETURN) {
            this.returnIndex = this.waypointIndex;
            this.state = ENEMY_STATE.STAGGER;
            this.staggerMs = STAGGER_MS;
        }
    }

    update(dtMs) {
        if (!this.alive || this.finished) {
            return;
        }
        this.ageMs += dtMs;
        if (this.state === ENEMY_STATE.STAGGER) {
            this.staggerMs -= dtMs;
            if (this.staggerMs <= 0) {
                this.state = ENEMY_STATE.RETURN;
            }
            return;
        }
        this._step(dtMs / 1000);
    }

    _step(dtSec) {
        const index = this.state === ENEMY_STATE.RETURN ? this.returnIndex : this.waypointIndex;
        if (index >= this.waypoints.length) {
            this._leak();
            return;
        }
        const [targetX, targetY] = this.waypoints[index];
        const gap = distance(this.x, this.y, targetX, targetY);
        const step = this.speed * dtSec;
        if (this.speed <= 0 || step <= 0) {
            this._noteStuck();
            return;
        }
        if (gap <= step) {
            this.x = targetX;
            this.y = targetY;
            this.stuckSteps = 0;
            this._advance(index);
            return;
        }
        const before = gap;
        this.x += ((targetX - this.x) / gap) * step;
        this.y += ((targetY - this.y) / gap) * step;
        const after = distance(this.x, this.y, targetX, targetY);
        if (after >= before - 0.001) {
            this._noteStuck();
        } else {
            this.stuckSteps = 0;
        }
    }

    _advance(index) {
        if (this.state === ENEMY_STATE.RETURN) {
            this.waypointIndex = index + 1;
            this.returnIndex = this.waypointIndex;
            this.state = ENEMY_STATE.MARCH;
        } else {
            this.waypointIndex = index + 1;
        }
        if (this.waypointIndex >= this.waypoints.length) {
            this._leak();
        }
    }

    /** Нулевая скорость или точка, к которой шаг не приближает, не держат монстра вечно. */
    _noteStuck() {
        this.stuckSteps += 1;
        if (this.stuckSteps < 5) {
            return;
        }
        this.stuckSteps = 0;
        const index = this.state === ENEMY_STATE.RETURN ? this.returnIndex : this.waypointIndex;
        this._advance(index);
    }

    _leak() {
        this.finished = true;
        this.state = ENEMY_STATE.LEAKED;
    }
}
