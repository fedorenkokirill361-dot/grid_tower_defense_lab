/** Поле: клетки, тропа, загрузка JSON. Рисует его уже виджет, не этот модуль. */

import {
    GENERATOR_CELL,
    GRID_COLUMNS,
    GRID_ROWS,
    PATH_CORNERS,
    TILE_SIZE,
    TOWER_COST,
    TOWER_DAMAGE,
    ATTACK_RADIUS,
    WAVES,
} from './constants.js';

function asNumber(value, name) {
    if (typeof value !== 'number' || Number.isNaN(value)) {
        throw new Error(`Поле ${name} должно быть числом`);
    }
    return value;
}

function cellsOnSegment(start, end) {
    const [col1, row1] = start;
    const [col2, row2] = end;
    const cells = [];
    if (col1 === col2) {
        const step = row2 >= row1 ? 1 : -1;
        for (let row = row1; row !== row2 + step; row += step) {
            cells.push([col1, row]);
        }
    } else if (row1 === row2) {
        const step = col2 >= col1 ? 1 : -1;
        for (let col = col1; col !== col2 + step; col += step) {
            cells.push([col, row1]);
        }
    } else {
        throw new Error('Опорные точки тропы должны стоять на одной прямой');
    }
    return cells;
}

export function buildPathCells(corners) {
    const cells = [];
    for (let i = 0; i < corners.length - 1; i += 1) {
        let segment = cellsOnSegment(corners[i], corners[i + 1]);
        if (cells.length > 0) {
            segment = segment.slice(1);
        }
        cells.push(...segment);
    }
    return cells;
}

export class GameField {
    constructor(config) {
        this.path = config.path;
        this.generatorCell = config.generator;
        this.waves = config.waves;
        this.tower = config.tower;
        this.pathCells = new Set(buildPathCells(this.path).map(([col, row]) => `${col},${row}`));
    }

    cellCenter(col, row) {
        return [col * TILE_SIZE + TILE_SIZE / 2, row * TILE_SIZE + TILE_SIZE / 2];
    }

    get waypoints() {
        return this.path.map(([col, row]) => this.cellCenter(col, row));
    }

    get generator() {
        return this.cellCenter(this.generatorCell[0], this.generatorCell[1]);
    }

    cellFromPixel(px, py) {
        const col = Math.floor(px / TILE_SIZE);
        const row = Math.floor(py / TILE_SIZE);
        if (col < 0 || row < 0 || col >= GRID_COLUMNS || row >= GRID_ROWS) {
            return null;
        }
        return [col, row];
    }

    isBuildable(col, row) {
        if (col < 0 || row < 0 || col >= GRID_COLUMNS || row >= GRID_ROWS) {
            return false;
        }
        if (this.pathCells.has(`${col},${row}`)) {
            return false;
        }
        return col !== this.generatorCell[0] || row !== this.generatorCell[1];
    }

    static fromJSON(text) {
        let config;
        try {
            config = JSON.parse(text);
        } catch (error) {
            throw new Error(`Ошибка парсинга JSON: ${error.message}`);
        }
        GameField.validate(config);
        return new GameField(config);
    }

    static validate(config) {
        if (!config || typeof config !== 'object') {
            throw new Error('Корень JSON должен быть объектом');
        }
        if (!Array.isArray(config.path) || config.path.length < 2) {
            throw new Error('path должен содержать минимум две точки');
        }
        for (const point of config.path) {
            if (!Array.isArray(point) || point.length !== 2) {
                throw new Error('Точка path задаётся парой [столбец, строка]');
            }
            asNumber(point[0], 'path.col');
            asNumber(point[1], 'path.row');
        }
        if (!Array.isArray(config.generator) || config.generator.length !== 2) {
            throw new Error('generator задаётся парой [столбец, строка]');
        }
        asNumber(config.generator[0], 'generator.col');
        asNumber(config.generator[1], 'generator.row');
        if (!Array.isArray(config.waves) || config.waves.length === 0) {
            throw new Error('waves должен быть непустым списком');
        }
        for (const wave of config.waves) {
            asNumber(wave.count, 'waves.count');
            asNumber(wave.hp, 'waves.hp');
            asNumber(wave.speed, 'waves.speed');
            asNumber(wave.reward, 'waves.reward');
        }
        if (!config.tower) {
            throw new Error('Нет объекта tower');
        }
        asNumber(config.tower.cost, 'tower.cost');
        asNumber(config.tower.damage, 'tower.damage');
        asNumber(config.tower.radius, 'tower.radius');
    }

    static defaults() {
        return new GameField({
            path: PATH_CORNERS,
            generator: GENERATOR_CELL,
            waves: WAVES,
            tower: {
                name: 'Лазер',
                cost: TOWER_COST,
                damage: TOWER_DAMAGE,
                radius: ATTACK_RADIUS,
                energyType: 'луч',
            },
        });
    }
}
