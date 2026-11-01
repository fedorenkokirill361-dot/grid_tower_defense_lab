/** Партия без отрисовки: спавн, питание, выстрелы, победа и поражение. */

import {
    BASE_HP,
    FIRST_WAVE_DELAY_MS,
    SPAWN_INTERVAL_MS,
    START_GOLD,
    STATE_DEFEAT,
    STATE_PLAY,
    STATE_VICTORY,
    WAVE_PAUSE_MS,
} from './constants.js';
import { EnergyGrid } from './energy_grid.js';
import { Enemy } from './enemy.js';
import { Stats } from './stats.js';
import { Tower } from './tower.js';

export class Game {
    constructor(field) {
        this.field = field;
        this.grid = new EnergyGrid(field.generator);
        this.reset();
    }

    reset() {
        this.gold = START_GOLD;
        this.baseHp = BASE_HP;
        this.baseHpMax = BASE_HP;
        this.state = STATE_PLAY;
        this.enemies = [];
        this.towers = [];
        this.beams = [];
        this.stats = new Stats();
        this.timeMs = 0;
        this.currentWave = 0;
        this.spawnedInWave = 0;
        this.lastStartedWave = 0;
        this.spawnTimer = FIRST_WAVE_DELAY_MS;
        this.energyScale = 1;
        this.attackScale = 1;
        this.damageModifier = 1;
        this.energyBoostMs = 0;
        this.attackBoostMs = 0;
        this.notice = '';
        this.grid.links = [];
    }

    get defaultSpec() {
        return {
            name: this.field.tower.name || 'Лазер',
            cost: this.field.tower.cost,
            damage: this.field.tower.damage,
            radius: this.field.tower.radius,
            energyType: this.field.tower.energyType || 'луч',
        };
    }

    tryBuild(col, row, spec = this.defaultSpec) {
        if (this.state !== STATE_PLAY) {
            return 'Сейчас нельзя строить';
        }
        if (!this.field.isBuildable(col, row)) {
            return 'На этой клетке строить нельзя';
        }
        if (this.towers.some((tower) => tower.col === col && tower.row === row)) {
            return 'Эта клетка уже занята';
        }
        if (this.gold < spec.cost) {
            return 'Не хватает золота';
        }
        this.gold -= spec.cost;
        this.towers.push(new Tower(col, row, spec, this.field.cellCenter(col, row)));
        this.stats.builds += 1;
        this.stats.add('build', { col, row, name: spec.name });
        this.notice = '';
        return '';
    }

    step(dtMs) {
        const ms = Math.min(Math.max(dtMs, 0), 100);
        this.timeMs += ms;
        this._tickBoosts(ms);
        for (const beam of this.beams) {
            beam.update(ms);
        }
        this.beams = this.beams.filter((beam) => beam.active);
        if (this.state !== STATE_PLAY) {
            return;
        }
        this._spawn(ms);
        for (const enemy of this.enemies) {
            enemy.update(ms);
        }
        this.grid.power(this.towers, this.energyScale);
        for (const tower of this.towers) {
            const beam = tower.act(this.timeMs, this.enemies, this.damageModifier, this.attackScale);
            if (beam) {
                this.beams.push(beam);
                this.stats.shots += 1;
                this.stats.add('shot', { col: tower.col, row: tower.row });
            }
        }
        this._resolve();
        this._outcome();
    }

    _tickBoosts(ms) {
        if (this.energyBoostMs > 0) {
            this.energyBoostMs -= ms;
            if (this.energyBoostMs <= 0) {
                this.energyScale = 1;
            }
        }
        if (this.attackBoostMs > 0) {
            this.attackBoostMs -= ms;
            if (this.attackBoostMs <= 0) {
                this.attackScale = 1;
            }
        }
    }

    _spawn(ms) {
        if (this.currentWave >= this.field.waves.length) {
            return;
        }
        this.spawnTimer -= ms;
        if (this.spawnTimer > 0) {
            return;
        }
        const spec = this.field.waves[this.currentWave];
        this.enemies.push(new Enemy(this.field.waypoints, spec.hp, spec.speed, spec.reward));
        this.lastStartedWave = this.currentWave + 1;
        this.spawnedInWave += 1;
        this.stats.add('spawn', { wave: this.lastStartedWave });
        if (this.spawnedInWave >= spec.count) {
            this.currentWave += 1;
            this.spawnedInWave = 0;
            this.spawnTimer = WAVE_PAUSE_MS;
        } else {
            this.spawnTimer = SPAWN_INTERVAL_MS;
        }
    }

    _resolve() {
        const kept = [];
        for (const enemy of this.enemies) {
            if (!enemy.alive) {
                this.gold += enemy.reward;
                this.stats.kills += 1;
                this.stats.add('kill', { reward: enemy.reward });
                continue;
            }
            if (enemy.finished) {
                this.baseHp -= 1;
                this.stats.leaks += 1;
                this.stats.add('leak', {});
                continue;
            }
            kept.push(enemy);
        }
        this.enemies = kept;
    }

    _outcome() {
        if (this.baseHp <= 0) {
            this.baseHp = 0;
            this.state = STATE_DEFEAT;
            this.stats.add('defeat', { wave: this.lastStartedWave });
            return;
        }
        const wavesDone = this.currentWave >= this.field.waves.length;
        if (wavesDone && this.enemies.length === 0) {
            this.state = STATE_VICTORY;
            this.stats.add('victory', {});
        }
    }
}
