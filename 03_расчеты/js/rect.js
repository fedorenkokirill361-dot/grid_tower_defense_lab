/** Прямоугольник без Pygame. move возвращает копию: пробный шаг не двигает оригинал. */

export class Rect {
    constructor(x, y, w, h) {
        this.x = x;
        this.y = y;
        this.w = w;
        this.h = h;
    }

    get centerx() {
        return this.x + this.w / 2;
    }

    get centery() {
        return this.y + this.h / 2;
    }

    get center() {
        return [this.centerx, this.centery];
    }

    move(dx, dy) {
        return new Rect(this.x + dx, this.y + dy, this.w, this.h);
    }

    colliderect(other) {
        return this.x < other.x + other.w
            && this.x + this.w > other.x
            && this.y < other.y + other.h
            && this.y + this.h > other.y;
    }

    collidepoint(px, py) {
        return px >= this.x && px < this.x + this.w && py >= this.y && py < this.y + this.h;
    }
}

/**
 * Сдвиг по осям по отдельности. Если по X упёрлись в стену, X не меняется,
 * а Y всё ещё можно пройти — сущность скользит вдоль препятствия, а не застревает.
 */
export function slide(rect, dx, dy, walls) {
    let next = rect.move(dx, 0);
    if (walls.some((wall) => next.colliderect(wall))) {
        next = rect;
    }
    const afterX = next;
    next = afterX.move(0, dy);
    if (walls.some((wall) => next.colliderect(wall))) {
        return afterX;
    }
    return next;
}

/** Рамка вокруг поля. Внешняя область сплошная, поэтому длинный шаг не перепрыгивает стену. */
export function borderWalls(width, height) {
    const span = 10000;
    return [
        new Rect(-span, -span, span, height + span * 2),
        new Rect(width, -span, span, height + span * 2),
        new Rect(0, -span, width, span),
        new Rect(0, height, width, span),
    ];
}
