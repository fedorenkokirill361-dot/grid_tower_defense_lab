/** Именованные команды виджета. Кнопки и консоль вызывают одни и те же функции. */

export function createScenarios(widget) {
    return {
        pause() {
            widget.paused = !widget.paused;
        },
        callWave() {
            widget.game.spawnTimer = 0;
        },
        laserVolley() {
            for (const tower of widget.game.towers) {
                tower.forceShot = true;
            }
        },
        powerSurge() {
            widget.game.energyScale = 0.5;
            widget.game.energyBoostMs = 4000;
        },
        revealMap() {
            widget.revealMs = 5000;
        },
        grantGold() {
            widget.game.gold += 80;
        },
    };
}

export function bindScenarioButtons(root, scenarios) {
    for (const button of root.querySelectorAll('[data-scenario]')) {
        button.addEventListener('click', () => {
            const action = scenarios[button.dataset.scenario];
            if (action) {
                action();
            }
        });
    }
}
