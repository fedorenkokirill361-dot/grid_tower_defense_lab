/** Показатели партии. Узлы уже есть в разметке, каждый кадр меняется только текст и ширина. */

export function updateHud(game, nodes) {
    if (!nodes?.gold) {
        return;
    }
    const ratio = game.baseHpMax > 0 ? game.baseHp / game.baseHpMax : 0;
    nodes.gold.textContent = String(game.gold);
    const waveNo = game.lastStartedWave || (game.currentWave > 0 ? game.currentWave : 0);
    nodes.wave.textContent = `${waveNo} / ${game.field.waves.length}`;
    nodes.base.textContent = String(game.baseHp);
    nodes.meter.style.width = `${Math.round(ratio * 100)}%`;
    const band = ratio < 0.33 ? 'low' : ratio < 0.66 ? 'mid' : 'high';
    nodes.meter.className = `meter-fill ${band}`;
    if (nodes.caption) {
        nodes.caption.textContent = band === 'low' ? 'критическое' : band === 'mid' ? 'среднее' : 'устойчивое';
    }
    if (nodes.waveMeter) {
        const progress = game.field.waves.length ? game.currentWave / game.field.waves.length : 0;
        nodes.waveMeter.style.width = `${Math.round(progress * 100)}%`;
    }
    if (nodes.status) {
        const names = { play: 'бой', victory: 'волны отбиты', defeat: 'база разрушена' };
        nodes.status.textContent = names[game.state] || game.state;
    }
}

export function hudNodes(root = document) {
    return {
        gold: root.querySelector('#gold'),
        wave: root.querySelector('#wave'),
        base: root.querySelector('#base'),
        meter: root.querySelector('#meter'),
        caption: root.querySelector('#meter-caption'),
        waveMeter: root.querySelector('#wave-meter'),
        status: root.querySelector('#status'),
    };
}
