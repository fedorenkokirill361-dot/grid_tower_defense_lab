/** Флаги зажатых клавиш. Цикл их опрашивает, а не двигает поле из самого keydown. */

const BLOCKED = new Set([
    'w', 'a', 's', 'd',
    'arrowup', 'arrowdown', 'arrowleft', 'arrowright',
    ' ',
]);

export function createInput(target = window) {
    const keys = {};

    const onDown = (event) => {
        const key = event.key.toLowerCase();
        keys[key] = true;
        if (BLOCKED.has(key)) {
            event.preventDefault();
        }
    };
    const onUp = (event) => {
        keys[event.key.toLowerCase()] = false;
    };

    target.addEventListener('keydown', onDown);
    target.addEventListener('keyup', onUp);

    return {
        read() {
            return {
                up: keys.w === true || keys.arrowup === true,
                down: keys.s === true || keys.arrowdown === true,
                left: keys.a === true || keys.arrowleft === true,
                right: keys.d === true || keys.arrowright === true,
                restart: keys.r === true,
            };
        },
        release(name) {
            keys[name] = false;
        },
    };
}
