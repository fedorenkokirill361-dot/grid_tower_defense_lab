/** Карточки типов башен из того же LocalStorage, что и страница каталога. */

import { escapeHtml, seedIfEmpty } from '../../05_каталог/js/catalog.js';

export function mountHotbar(container, onSelect) {
    let selectedId = null;
    let lastRaw = '';

    const paint = () => {
        const items = seedIfEmpty();
        const raw = JSON.stringify(items);
        const missing = selectedId && !items.some((item) => item.id === selectedId);
        if (missing) {
            selectedId = items[0]?.id ?? null;
            if (items[0]) {
                onSelect(items[0]);
            }
        }
        if (!selectedId && items[0]) {
            selectedId = items[0].id;
            onSelect(items[0]);
        }
        if (raw === lastRaw && container.dataset.selected === (selectedId || '')) {
            return;
        }
        lastRaw = raw;
        container.dataset.selected = selectedId || '';
        container.innerHTML = items.length
            ? items.map((item) => `
                <button type="button" class="hotbar-card${item.id === selectedId ? ' selected' : ''}" data-id="${escapeHtml(item.id)}">
                    <span class="card-name">${escapeHtml(item.name)}</span>
                    <span class="card-stats">урон ${item.damage} · R ${item.radius} · ${escapeHtml(item.energyType)} · ${item.cost}</span>
                </button>`).join('')
            : '<p class="muted">Каталог пуст. Добавьте тип на странице каталога.</p>';
    };

    container.addEventListener('click', (event) => {
        const card = event.target.closest('.hotbar-card');
        if (!card) {
            return;
        }
        selectedId = card.dataset.id;
        const item = seedIfEmpty().find((entry) => entry.id === selectedId);
        if (item) {
            onSelect(item);
        }
        lastRaw = '';
        paint();
    });

    window.addEventListener('storage', () => {
        lastRaw = '';
        paint();
    });
    window.addEventListener('focus', () => {
        lastRaw = '';
        paint();
    });
    setInterval(paint, 1000);
    paint();
}
