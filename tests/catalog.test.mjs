/* Проверяет воспроизводимость каталога из JSON-источников. §catalog */
import { spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');

describe('project catalog', () => {
  it('matches its JSON sources', () => {
    const result = spawnSync(process.execPath, ['scripts/generateComponentCatalog.mjs', '--check'], {
      cwd: repoRoot,
      encoding: 'utf8',
    });
    assert.equal(result.status, 0, result.stderr || result.stdout);
  });

  it('uses continuous component IDs and one selected climate module', () => {
    const source = JSON.parse(fs.readFileSync(resolve(repoRoot, 'catalog/components.json'), 'utf8'));
    const ids = source.components.map(item => item.id).sort();
    assert.equal(ids.length, 23);
    assert.deepEqual(ids, Array.from({ length: 23 }, (_, index) => `cmp-${String(index + 1).padStart(3, '0')}`));
    assert.equal(source.components.filter(item => item.name.includes('AHT20 + BMP280')).length, 1);
    assert.equal(source.components.some(item => /NTC 10k B3950|GY-BME\/P280|SHT20 standalone/i.test(item.name)), false);
  });

  it('contains categories, requested columns, drawings and lazy 3D controls', () => {
    const html = fs.readFileSync(resolve(repoRoot, 'catalog/catalog.html'), 'utf8');
    for (const heading of ['ID', 'Картинка', 'Возможные названия компонента', 'Зачем он нужен', 'Описание или покупка']) {
      assert.match(html, new RegExp(`<th>${heading}</th>`));
    }
    for (const category of ['Управление и датчики', 'Питание и коммутация', 'Подсветка', 'Механика', 'Герметизация и монтаж', 'Ткани', 'Материалы для 3D-печати']) {
      assert.match(html, new RegExp(category));
    }
    assert.match(html, /Bearing 6804-2RS \(candidate\)/);
    assert.match(html, /внутренний диаметр d = 20 мм, наружный D = 32 мм, ширина B = 7 мм/);
    assert.match(html, /2RS — резиновые уплотнения с обеих сторон/);
    assert.match(html, /Компоненты/);
    assert.match(html, /Чертежи и 3D/);
    assert.match(html, /Схема соединений электроники — A4/);
    assert.match(html, /flagpole_finial_v0_5_assembly\.glb/);
    assert.match(html, /data-src="\.\.\/mechanical\/flagpole_finial_v0_5_assembly\.glb"/);
    assert.match(html, /model-viewer\/4\.2\.0\/model-viewer\.min\.js/);
    assert.match(html, /Загрузить интерактивную 3D-модель/);
    assert.match(html, /Porex Virtek PMV25 hydrophobic PTFE vent membrane/);
    assert.match(html, /MOLYKOTE 111 silicone compound for seals/);
    assert.match(html, /A2 stainless M3\/M4 screw, washer and nyloc nut kit/);
    assert.match(html, /Flexible silicone power wire kit — 2×0\.75 mm² and AWG20/);
    assert.match(html, /Four-color flexible sensor wire — AWG26–28/);
    assert.match(html, /Строительная кровельная или стеновая мембрана для этой детали не выбирается/);
  });
});
