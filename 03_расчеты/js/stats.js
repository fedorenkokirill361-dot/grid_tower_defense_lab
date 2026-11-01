/** Счётчик событий партии. Виджет его показывает, сам список от Canvas не зависит. */

export class Stats {
    constructor() {
        this.shots = 0;
        this.kills = 0;
        this.leaks = 0;
        this.builds = 0;
        this.events = [];
    }

    add(type, payload = {}) {
        this.events.push({ type, ...payload });
    }
}
