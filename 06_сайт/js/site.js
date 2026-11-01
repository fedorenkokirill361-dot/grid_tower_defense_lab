/** Шапка сайта: на узком экране ссылки прячутся за кнопкой меню. */

export function bindChrome(root = document) {
    const burger = root.querySelector('#burger');
    const menu = root.querySelector('#mobile-menu');
    if (!burger || !menu) {
        return;
    }
    burger.addEventListener('click', () => {
        menu.classList.toggle('open');
    });
    for (const link of menu.querySelectorAll('a')) {
        link.addEventListener('click', () => menu.classList.remove('open'));
    }
}
