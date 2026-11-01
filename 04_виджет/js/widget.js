/** Холст обороны. Считает ядро из 03_расчеты, здесь только ввод, шаг и рисунок. */

import { Commander } from '../../03_расчеты/js/commander.js';
import { FIELD_HEIGHT, FIELD_WIDTH, TILE_SIZE } from '../../03_расчеты/js/constants.js';
import { distance } from '../../03_расчеты/js/formulas.js';
import { Game } from '../../03_расчеты/js/game.js';
import { GameField } from '../../03_расчеты/js/game_field.js';
import { borderWalls } from '../../03_расчеты/js/rect.js';
import { loadCatalog, seedIfEmpty } from '../../05_каталог/js/catalog.js';
import { hudNodes, updateHud } from './hud.js';
import { createInput } from './input.js';
import { bindScenarioButtons, createScenarios } from './scenarios.js';

const FRAME_MS = 1000 / 60;
const VISIBLE_RADIUS = 280;

export class Widget {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.game = new Game(options.field || GameField.defaults());
        const origin = this.game.field.cellCenter(10, 6);
        this.commander = new Commander(origin[0], origin[1]);
        this.walls = borderWalls(FIELD_WIDTH, FIELD_HEIGHT);
        this.input = options.input || createInput();
        this.paused = false;
        this.revealMs = 0;
        this.buildSpec = null;
        this.hover = null;
        this.notice = '';
        this.onFrame = options.onFrame || null;
        this.scenarios = createScenarios(this);
        this.hud = options.hud || hudNodes();
        canvas.addEventListener('click', (event) => this._click(event));
        canvas.addEventListener('mousemove', (event) => {
            this.hover = this._cell(event);
        });
    }

    setBuildSpec(spec) {
        this.buildSpec = spec ? { ...spec } : null;
    }

    currentSpec() {
        if (this.buildSpec) {
            return this.buildSpec;
        }
        return loadCatalog()[0] || this.game.defaultSpec;
    }

    restart() {
        this.game.reset();
        this.notice = '';
        this.paused = false;
    }

    start(root = document) {
        seedIfEmpty();
        bindScenarioButtons(root, this.scenarios);
        const restart = root.querySelector('#restart');
        if (restart) {
            restart.addEventListener('click', () => this.restart());
        }
        let last = performance.now();
        let accumulator = 0;
        const loop = (now) => {
            const delta = Math.min(now - last, 100);
            last = now;
            accumulator += delta;
            while (accumulator >= FRAME_MS) {
                this._tick(FRAME_MS);
                accumulator -= FRAME_MS;
            }
            this._draw();
            requestAnimationFrame(loop);
        };
        requestAnimationFrame(loop);
    }

    _tick(dtMs) {
        if (this.revealMs > 0) {
            this.revealMs -= dtMs;
        }
        const stick = this.input.read();
        if (stick.restart) {
            this.restart();
            this.input.release('r');
        }
        const dirX = (stick.right ? 1 : 0) - (stick.left ? 1 : 0);
        const dirY = (stick.down ? 1 : 0) - (stick.up ? 1 : 0);
        this.commander.step(dirX, dirY, dtMs, this.walls);
        if (!this.paused) {
            this.game.step(dtMs);
        }
        if (this.game.notice) {
            this.notice = this.game.notice;
        }
        updateHud(this.game, this.hud);
        if (this.onFrame) {
            this.onFrame(this.game);
        }
    }

    _cell(event) {
        const box = this.canvas.getBoundingClientRect();
        const x = (event.clientX - box.left) * (this.canvas.width / box.width);
        const y = (event.clientY - box.top) * (this.canvas.height / box.height);
        return this.game.field.cellFromPixel(x, y);
    }

    _click(event) {
        const cell = this._cell(event);
        if (!cell) {
            return;
        }
        const message = this.game.tryBuild(cell[0], cell[1], this.currentSpec());
        this.notice = message;
        this.game.notice = message;
    }

    _visible(x, y) {
        const radius = this.revealMs > 0 ? 4000 : VISIBLE_RADIUS;
        return distance(x, y, this.commander.x, this.commander.y) <= radius;
    }

    _draw() {
        const ctx = this.ctx;
        const field = this.game.field;
        ctx.fillStyle = '#101418';
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        for (let row = 0; row < 14; row += 1) {
            for (let col = 0; col < 20; col += 1) {
                const [cx, cy] = field.cellCenter(col, row);
                if (!this._visible(cx, cy)) {
                    continue;
                }
                const onPath = field.pathCells.has(`${col},${row}`);
                ctx.fillStyle = onPath ? '#6e5842' : '#1a222b';
                ctx.fillRect(col * TILE_SIZE + 1, row * TILE_SIZE + 1, TILE_SIZE - 2, TILE_SIZE - 2);
            }
        }

        const generator = field.generator;
        if (this._visible(generator[0], generator[1])) {
            ctx.fillStyle = '#ffc44a';
            ctx.beginPath();
            ctx.arc(generator[0], generator[1], 14, 0, Math.PI * 2);
            ctx.fill();
        }

        ctx.lineWidth = 1.5;
        for (const link of this.game.grid.links) {
            if (!this._visible(link.x1, link.y1) && !this._visible(link.x2, link.y2)) {
                continue;
            }
            ctx.strokeStyle = 'rgba(58, 160, 255, 0.95)';
            ctx.beginPath();
            ctx.moveTo(link.x1, link.y1);
            ctx.lineTo(link.x2, link.y2);
            ctx.stroke();
        }

        for (const tower of this.game.towers) {
            if (!this._visible(tower.x, tower.y)) {
                continue;
            }
            ctx.fillStyle = tower.powered ? '#49b0dc' : '#66707c';
            ctx.fillRect(tower.x - 11, tower.y - 11, 22, 22);
            if (tower.state === 'Aim' || tower.state === 'Cooldown') {
                const pulse = 0.35 + 0.65 * Math.abs(Math.sin(this.game.timeMs / 140));
                ctx.fillStyle = `rgba(255, 214, 90, ${pulse.toFixed(3)})`;
                ctx.beginPath();
                ctx.arc(tower.x, tower.y - 20, 4, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        if (this.hover && field.isBuildable(this.hover[0], this.hover[1])) {
            const [hx, hy] = field.cellCenter(this.hover[0], this.hover[1]);
            if (this._visible(hx, hy)) {
                ctx.strokeStyle = 'rgba(73, 176, 220, 0.7)';
                ctx.beginPath();
                ctx.arc(hx, hy, this.currentSpec().radius, 0, Math.PI * 2);
                ctx.stroke();
            }
        }

        for (const enemy of this.game.enemies) {
            if (!this._visible(enemy.x, enemy.y)) {
                continue;
            }
            const appear = Math.min(1, enemy.ageMs / 220);
            ctx.globalAlpha = appear;
            ctx.fillStyle = '#d23c3c';
            ctx.beginPath();
            ctx.arc(enemy.x, enemy.y, 12 * Math.max(appear, 0.2), 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = 1;
            const ratio = enemy.maxHp > 0 ? Math.max(0, enemy.hp / enemy.maxHp) : 0;
            ctx.fillStyle = '#2a2a2a';
            ctx.fillRect(enemy.x - 11, enemy.y - 20, 22, 3);
            ctx.fillStyle = '#8dffb0';
            ctx.fillRect(enemy.x - 11, enemy.y - 20, 22 * ratio, 3);
        }

        for (const beam of this.game.beams) {
            if (!this._visible(beam.x1, beam.y1) && !this._visible(beam.x2, beam.y2)) {
                continue;
            }
            ctx.strokeStyle = `rgba(255, 72, 72, ${beam.alpha.toFixed(3)})`;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(beam.x1, beam.y1);
            ctx.lineTo(beam.x2, beam.y2);
            ctx.stroke();
        }

        ctx.fillStyle = '#f2d48a';
        ctx.beginPath();
        ctx.arc(this.commander.x, this.commander.y, 5, 0, Math.PI * 2);
        ctx.fill();

        if (this.notice) {
            ctx.fillStyle = '#f4f7f2';
            ctx.font = '16px Consolas, monospace';
            ctx.fillText(this.notice, 12, 24);
        }

        const result = document.querySelector('#result');
        if (result) {
            const done = this.game.state !== 'play';
            result.classList.toggle('hidden', !done);
            if (done) {
                result.textContent = this.game.state === 'victory' ? 'Волны отбиты' : 'База разрушена';
            }
        }
    }
}

export function boot(root = document) {
    const canvas = root.querySelector('#game');
    const widget = new Widget(canvas, { hud: hudNodes(root) });
    widget.start(root);
    window.DefenseHQ = { widget, scenarios: widget.scenarios };
    return widget;
}
