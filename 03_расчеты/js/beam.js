/** Короткий луч выстрела. Виджет только читает alpha, время жизни считает ядро. */

export class Beam {
    constructor(x1, y1, x2, y2, lifeMs = 180) {
        this.x1 = x1;
        this.y1 = y1;
        this.x2 = x2;
        this.y2 = y2;
        this.lifeMs = lifeMs;
        this.ageMs = 0;
        this.active = true;
    }

    update(dtMs) {
        this.ageMs += dtMs;
        if (this.ageMs >= this.lifeMs) {
            this.active = false;
        }
    }

    get alpha() {
        return Math.max(0, 1 - this.ageMs / this.lifeMs);
    }
}
