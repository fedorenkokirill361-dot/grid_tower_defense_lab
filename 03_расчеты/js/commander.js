/** Точка обзора на поле. Упирается в рамку и скользит вдоль неё, а не застревает в углу. */

import { slide, Rect } from './rect.js';

export class Commander {
    constructor(x, y) {
        this.rect = new Rect(x - 8, y - 8, 16, 16);
        this.speed = 220;
    }

    get x() {
        return this.rect.centerx;
    }

    get y() {
        return this.rect.centery;
    }

    step(dirX, dirY, dtMs, walls) {
        if (dirX === 0 && dirY === 0) {
            return;
        }
        const length = Math.hypot(dirX, dirY);
        const scale = this.speed * (dtMs / 1000);
        this.rect = slide(
            this.rect,
            (dirX / length) * scale,
            (dirY / length) * scale,
            walls,
        );
    }
}
