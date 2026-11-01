/** Таблица типов башен: создание, правка строки, удаление, фильтр, LocalStorage. */

import {
    escapeHtml,
    loadCatalog,
    saveCatalog,
    seedIfEmpty,
    validateTower,
} from './catalog.js';

function showErrors(form, errors) {
    for (const field of ['name', 'damage', 'radius', 'energyType', 'cost']) {
        const slot = form.querySelector(`[data-error="${field}"]`);
        if (slot) {
            slot.textContent = errors[field] || '';
        }
    }
}

function viewRow(item) {
    return `
        <tr data-id="${escapeHtml(item.id)}">
            <td>${escapeHtml(item.name)}</td>
            <td>${item.damage}</td>
            <td>${item.radius}</td>
            <td>${escapeHtml(item.energyType)}</td>
            <td>${item.cost}</td>
            <td>
                <button type="button" class="btn-edit" data-id="${escapeHtml(item.id)}">Править</button>
                <button type="button" class="btn-delete" data-id="${escapeHtml(item.id)}">Удалить</button>
            </td>
        </tr>`;
}

function editRow(item) {
    return `
        <tr data-id="${escapeHtml(item.id)}" class="editing">
            <td><input name="name" value="${escapeHtml(item.name)}" required></td>
            <td><input name="damage" type="number" min="1" max="200" value="${item.damage}" required></td>
            <td><input name="radius" type="number" min="40" max="300" value="${item.radius}" required></td>
            <td><input name="energyType" value="${escapeHtml(item.energyType)}" required></td>
            <td><input name="cost" type="number" min="1" max="500" value="${item.cost}" required></td>
            <td>
                <button type="button" class="btn-save" data-id="${escapeHtml(item.id)}">Сохранить</button>
                <button type="button" class="btn-cancel" data-id="${escapeHtml(item.id)}">Отмена</button>
            </td>
        </tr>`;
}

export function mountCrud(root = document) {
    const form = root.querySelector('#create-form');
    const tbody = root.querySelector('#towers tbody');
    const radius = root.querySelector('#filter-radius');
    const radiusOut = root.querySelector('#filter-radius-value');
    const search = root.querySelector('#filter-name');
    if (!form || !tbody) {
        return;
    }
    let editingId = null;
    seedIfEmpty();

    function render() {
        const maxRadius = Number(radius?.value ?? 300);
        const query = (search?.value ?? '').trim().toLowerCase();
        if (radiusOut) {
            radiusOut.textContent = String(maxRadius);
        }
        const rows = loadCatalog().filter((item) => {
            if (item.id === editingId) {
                return true;
            }
            const byRadius = item.radius <= maxRadius;
            const byName = item.name.toLowerCase().includes(query);
            return byRadius && byName;
        });
        tbody.innerHTML = rows.map((item) => (item.id === editingId ? editRow(item) : viewRow(item))).join('');
    }

    form.addEventListener('submit', (event) => {
        event.preventDefault();
        const data = Object.fromEntries(new FormData(form).entries());
        const result = validateTower(data);
        showErrors(form, result.errors);
        if (!result.valid) {
            return;
        }
        const items = loadCatalog();
        items.push({ ...result.value, id: crypto.randomUUID() });
        saveCatalog(items);
        form.reset();
        showErrors(form, {});
        render();
    });

    tbody.addEventListener('click', (event) => {
        const button = event.target.closest('button');
        if (!button) {
            return;
        }
        const id = button.dataset.id;
        const items = loadCatalog();
        if (button.classList.contains('btn-edit')) {
            editingId = id;
            render();
            return;
        }
        if (button.classList.contains('btn-cancel')) {
            editingId = null;
            render();
            return;
        }
        if (button.classList.contains('btn-delete')) {
            if (!window.confirm('Удалить этот тип башни?')) {
                return;
            }
            saveCatalog(items.filter((item) => item.id !== id));
            if (editingId === id) {
                editingId = null;
            }
            render();
            return;
        }
        if (button.classList.contains('btn-save')) {
            const row = button.closest('tr');
            const data = {};
            for (const input of row.querySelectorAll('input')) {
                data[input.name] = input.value;
            }
            const result = validateTower(data);
            if (!result.valid) {
                window.alert(Object.values(result.errors).join('\n'));
                return;
            }
            saveCatalog(items.map((item) => (item.id === id ? { ...result.value, id } : item)));
            editingId = null;
            render();
        }
    });

    radius?.addEventListener('input', render);
    search?.addEventListener('input', render);
    window.addEventListener('storage', render);
    render();
}

if (document.querySelector('#towers')) {
    mountCrud(document);
}
