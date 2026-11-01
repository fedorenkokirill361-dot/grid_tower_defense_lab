/** Каталог типов башен. Ключ один и для CRUD, и для сайта. */

export const STORAGE_KEY = 'defense_towers';

export const DEFAULT_TOWERS = [
    { name: 'Лазер', damage: 18, radius: 120, energyType: 'луч', cost: 40 },
    { name: 'Пулемёт', damage: 10, radius: 80, energyType: 'кинетика', cost: 25 },
    { name: 'Мортира', damage: 35, radius: 160, energyType: 'разрыв', cost: 70 },
];

export function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

export function validateTower(data) {
    const errors = {};
    const name = String(data.name ?? '').trim();
    if (!name) {
        errors.name = 'Название обязательно';
    } else if (name.length > 24) {
        errors.name = 'Не длиннее 24 символов';
    }
    const damage = Number(data.damage);
    if (!Number.isFinite(damage) || damage < 1 || damage > 200) {
        errors.damage = 'Урон от 1 до 200';
    }
    const radius = Number(data.radius);
    if (!Number.isFinite(radius) || radius < 40 || radius > 300) {
        errors.radius = 'Радиус от 40 до 300';
    }
    const energyType = String(data.energyType ?? '').trim();
    if (!energyType) {
        errors.energyType = 'Тип энергии обязателен';
    } else if (energyType.length > 16) {
        errors.energyType = 'Не длиннее 16 символов';
    }
    const cost = Number(data.cost);
    if (!Number.isFinite(cost) || cost < 1 || cost > 500) {
        errors.cost = 'Цена от 1 до 500';
    }
    return {
        valid: Object.keys(errors).length === 0,
        errors,
        value: { name, damage, radius, energyType, cost },
    };
}

export function loadCatalog() {
    if (typeof localStorage === 'undefined') {
        return DEFAULT_TOWERS.map((item, index) => ({ ...item, id: `default-${index}` }));
    }
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
        return [];
    }
    try {
        const data = JSON.parse(raw);
        return Array.isArray(data) ? data : [];
    } catch (error) {
        console.error('Каталог не разобран', error);
        return [];
    }
}

export function saveCatalog(items) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

/** Пустое хранилище заполняется тремя типами из баланса игры. Уже сохранённый список не трогается. */
export function seedIfEmpty() {
    if (typeof localStorage === 'undefined') {
        return loadCatalog();
    }
    if (localStorage.getItem(STORAGE_KEY) === null) {
        const items = DEFAULT_TOWERS.map((item) => ({ ...item, id: crypto.randomUUID() }));
        saveCatalog(items);
        return items;
    }
    return loadCatalog();
}
