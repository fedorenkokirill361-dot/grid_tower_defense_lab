/** Главная страница: холст из виджета и магазин башен справа. */

import { boot } from '../../04_виджет/js/widget.js';
import { mountHotbar } from './hotbar.js';
import { bindChrome } from './site.js';
import { hudNodes, updateHud } from './hud.js';

bindChrome();

const widget = boot(document);
widget.onFrame = (game) => updateHud(game, hudNodes(document));

mountHotbar(document.querySelector('#shop'), (item) => {
    widget.setBuildSpec(item);
    widget.notice = `Строится: ${item.name}`;
});
