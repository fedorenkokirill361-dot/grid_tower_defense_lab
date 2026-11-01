/** Самопроверка ядра. Рисовать ничего не нужно: node selftest.js */

import { readFileSync } from 'node:fs';
import { Beam } from './js/beam.js';
import { Commander } from './js/commander.js';
import { borderWalls, Rect, slide } from './js/rect.js';
import { ENERGY_DECAY, ENEMY_STATE, STAGGER_MS, TOWER_STATE } from './js/constants.js';
import { Enemy } from './js/enemy.js';
import { EnergyGrid } from './js/energy_grid.js';
import {
    attackAt,
    attackLimit,
    distance,
    energyAt,
    energyLimit,
    energyLinkOk,
    shotConnects,
} from './js/formulas.js';
import { Game } from './js/game.js';
import { GameField } from './js/game_field.js';
import { Tower } from './js/tower.js';

let failed = 0;
let passed = 0;

function check(name, condition) {
    if (condition) {
        passed += 1;
        console.log(`OK  ${name}`);
        return;
    }
    failed += 1;
    console.log(`FAIL  ${name}`);
}

const field = GameField.defaults();
const spec = field.tower;

check('расстояние 3-4-5', distance(0, 0, 3, 4) === 5);
check('питание у генератора равно 1', energyAt(0) === 1);
check('предел питания совпадает с D=150', Math.abs(energyLimit() - 150) < 1e-6);
check('питание убывает с дистанцией', energyAt(0) > energyAt(50) && energyAt(50) > energyAt(120));
check('близкая башня получает связь', energyLinkOk(120));
check('на границе D связи нет', energyLinkOk(150) === false);
check('далёкая башня без связи', energyLinkOk(200) === false);
check('удвоение затухания сокращает предел вдвое', Math.abs(energyLimit(2) - 75) < 1e-6);
check('попадание у ствола равно 1', attackAt(0, 120) === 1);
check('выстрел на радиусе R проходит порог', shotConnects(120, 120));
check('выстрел дальше R не проходит', shotConnects(121, 120) === false);
check('двойное затухание гасит край радиуса', shotConnects(120, 120, 2) === false);
check('двойное затухание оставляет половину радиуса', shotConnects(60, 120, 2));
check('предел атаки при scale=2 равен R/2', attackLimit(120, 2) === 60);

const box = new Rect(10, 20, 30, 40);
const moved = box.move(5, -2);
check('move возвращает другой объект', moved !== box);
check('move не меняет оригинал', box.x === 10 && box.y === 20 && moved.x === 15 && moved.y === 18);
check('центр прямоугольника', box.centerx === 25 && box.centery === 40);
check('пересечение есть', box.colliderect(new Rect(20, 30, 10, 10)));
check('пересечения нет', box.colliderect(new Rect(100, 100, 5, 5)) === false);
check('точка внутри', box.collidepoint(10, 20));
check('точка снаружи', box.collidepoint(9, 20) === false);

const blocked = slide(new Rect(90, 0, 16, 16), 20, 0, [new Rect(100, -10, 40, 40)]);
check('упор в стену не двигает прямоугольник', blocked.x === 90);
const slipped = slide(new Rect(90, 0, 16, 16), 20, 10, [new Rect(100, -10, 40, 20)]);
check('вдоль стены остаётся сдвиг по свободной оси', slipped.x === 90 && slipped.y === 10);

const commander = new Commander(20, 20);
const walls = borderWalls(800, 560);
commander.step(-1, 0, 1000, walls);
check('командир не выходит за левую рамку', commander.x >= 8);

const walker = new Enemy([[0, 0], [100, 0], [100, 100]], 30, 50, 3);
walker.update(1000);
check('монстр проходит 50 px за секунду', Math.abs(walker.x - 50) < 1e-6 && walker.state === ENEMY_STATE.MARCH);
walker.takeDamage(5);
check('попадание запоминает точку возврата', walker.state === ENEMY_STATE.STAGGER && walker.returnIndex === 1);
walker.update(STAGGER_MS);
check('после остановки монстр переходит к возврату', walker.state === ENEMY_STATE.RETURN);
walker.update(2000);
check('возврат доводит до точки и снова включает марш', walker.state === ENEMY_STATE.MARCH && walker.waypointIndex === 2);

const stuck = new Enemy([[0, 0], [40, 0], [80, 0]], 10, 0, 1);
for (let i = 0; i < 5; i += 1) {
    stuck.update(100);
}
check('нулевая скорость не держит монстра на месте вечно', stuck.waypointIndex === 2);

const leaker = new Enemy([[0, 0], [10, 0]], 10, 1000, 1);
leaker.update(1000);
check('конец тропы помечает прорыв', leaker.finished && leaker.state === ENEMY_STATE.LEAKED);

const grid = new EnergyGrid(field.cellCenter(0, 0));
const near = new Tower(0, 3, spec, field.cellCenter(0, 3));
const relay = new Tower(0, 6, spec, field.cellCenter(0, 6));
const far = new Tower(19, 13, spec, field.cellCenter(19, 13));
grid.power([near]);
check('башня рядом с генератором запитана', near.powered);
near.powered = false;
grid.power([far]);
check('башня в углу без цепочки не запитана', far.powered === false);
grid.power([near, relay, far]);
check('цепочка BFS дотягивает питание через соседнюю башню', near.powered && relay.powered && far.powered === false);

const custom = new GameField({
    path: [[0, 1], [2, 1]],
    generator: [0, 5],
    waves: [{ count: 1, hp: 10, speed: 20, reward: 4 }],
    tower: spec,
});
const battle = new Game(custom);
check('на тропе строить нельзя', battle.tryBuild(0, 1, spec) !== '');
check('башня списывает золото', battle.tryBuild(0, 3, spec) === '' && battle.gold === 90);
battle.spawnTimer = 0;
battle.step(50);
check('запитанная башня убивает монстра в радиусе', battle.stats.kills === 1 && battle.towers[0].state === TOWER_STATE.COOLDOWN);
battle.step(50);
check('вторая волна не нужна: партия выиграна', battle.state === 'victory');

const quiet = new Game(custom);
quiet.tryBuild(19, 13, spec);
quiet.enemies.push(new Enemy(custom.waypoints, 40, 0, 1));
quiet.grid.power(quiet.towers);
quiet.towers[0].act(0, quiet.enemies);
check('башня без питания не наносит урон', quiet.enemies[0].hp === 40 && quiet.towers[0].state === TOWER_STATE.UNPOWERED);

const paced = new Tower(0, 3, spec, custom.cellCenter(0, 3));
paced.powered = true;
const dummy = new Enemy(custom.waypoints, 100, 0, 1);
dummy.speed = 0;
paced.act(0, [dummy]);
const afterFirst = dummy.hp;
paced.act(200, [dummy]);
check('кулдаун не даёт стрелять второй раз в ту же секунду', dummy.hp === afterFirst);
paced.act(1000, [dummy]);
check('через секунду выстрел снова проходит', dummy.hp === afterFirst - spec.damage);

const beam = new Beam(0, 0, 10, 0, 100);
check('у нового луча alpha равна 1', beam.alpha === 1);
beam.update(100);
check('луч гаснет по окончании жизни', beam.active === false && beam.alpha === 0);

const loss = new Game(custom);
loss.baseHp = 1;
loss.spawnTimer = 0;
loss.field.waves[0].speed = 10000;
loss.step(100);
check('прорыв обнуляет базу и завершает партию', loss.state === 'defeat' && loss.baseHp === 0);

const levelText = readFileSync(new URL('./level.json', import.meta.url), 'utf8');
const loaded = GameField.fromJSON(levelText);
check('level.json открывается и хранит 5 волн', loaded.waves.length === 5 && loaded.generatorCell[0] === 7);

let broken = false;
try {
    GameField.fromJSON('{');
} catch (error) {
    broken = error.message.includes('Ошибка парсинга JSON');
}
check('битый JSON не роняет проверку молча', broken);

let missing = false;
try {
    GameField.fromJSON('{"path":[[0,1],[1,1]]}');
} catch (error) {
    missing = error.message.includes('generator');
}
check('JSON без обязательного поля отклоняется', missing);

check('коэффициент затухания положительный', ENERGY_DECAY > 0);

console.log(`\n${passed} успешно, ${failed} с ошибкой`);
if (failed > 0) {
    process.exit(1);
}
