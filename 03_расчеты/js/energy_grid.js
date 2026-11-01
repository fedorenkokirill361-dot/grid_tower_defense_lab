/** Питание башен: поиск в ширину от генератора. Ребро есть, если формула выше порога. */

import { distance, energyLinkOk } from './formulas.js';

export class EnergyGrid {
    constructor(generator) {
        this.generator = { x: generator[0], y: generator[1] };
        this.links = [];
    }

    power(towers, scale = 1) {
        for (const tower of towers) {
            tower.powered = false;
        }
        this.links = [];
        const queue = [this.generator];
        let head = 0;
        while (head < queue.length) {
            const source = queue[head];
            head += 1;
            for (const tower of towers) {
                if (tower.powered) {
                    continue;
                }
                const gap = distance(source.x, source.y, tower.x, tower.y);
                if (!energyLinkOk(gap, scale)) {
                    continue;
                }
                tower.powered = true;
                this.links.push({
                    x1: source.x,
                    y1: source.y,
                    x2: tower.x,
                    y2: tower.y,
                });
                queue.push({ x: tower.x, y: tower.y });
            }
        }
    }
}
