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
    assert.equal(ids.length, 25);
    assert.deepEqual(ids, Array.from({ length: 25 }, (_, index) => String(index + 1).padStart(3, '0')));
    assert.equal(ids.every(id => /^\d{3}$/.test(id)), true);
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
    assert.match(html, /Схема соединений электроники v0\.7\.4 — A4/);
    assert.match(html, /flagpole_finial_v0_5_assembly\.glb/);
    assert.match(html, /data-src="\.\.\/mechanical\/flagpole_finial_v0_5_assembly\.glb"/);
    assert.match(html, /model-viewer\/4\.2\.0\/model-viewer\.min\.js/);
    assert.match(html, /Загрузить интерактивную 3D-модель/);
    assert.match(html, /Self-adhesive hydrophobic vent membrane — Ø20 mm \/ active Ø10 mm/);
    assert.match(html, /MOLYKOTE 111 silicone compound for seals/);
    assert.match(html, /A2 stainless M3\/M4 screws, washers and standard hex nuts for captive pockets/);
    assert.match(html, /Flexible silicone power wire kit — 2×0\.75 mm² and AWG20/);
    assert.match(html, /Four-color flexible sensor wire — AWG26–28/);
    assert.match(html, /Cut transparent window for the VEML7700 light well/);
    assert.match(html, /покупать отдельный материал не требуется/);
    assert.match(html, /UV-resistant bonded polyester sewing thread — Tex 45/);
    assert.match(html, /100% polyester\/PES, continuous filament, bonded/);
    assert.match(html, /Маршрут двух проводов питания флага v0\.7\.4/);
    assert.match(html, /Таблица идентификаторов печатных деталей v0\.7\.4/);
    assert.match(html, /Карта закладных гаек и крепежа v0\.7\.4/);
    assert.match(html, /Компоновка электроники в боксе v0\.7\.4/);
    assert.match(html, /актуально · v0\.7\.4/);
    assert.match(html, /история · v0\.5/);
    assert.match(html, /Раздельные очереди печати по материалам/);
    assert.match(html, /Очередь печати PETG/);
    assert.match(html, /Очередь печати TPU 95A/);
    assert.match(html, /Очередь печати TPU 85A/);
    assert.match(html, /нейлоновой основе/);
    assert.match(html, /320 кд\/\(лк·м²\)/);
    assert.match(html, /семь отверстий Ø2 мм/);
    assert.doesNotMatch(html, /\b(?:cmp|drw|mdl)-\d{3}\b/);
  });

  it('keeps drawing, model and print-session IDs unique and assets present', () => {
    const media = JSON.parse(fs.readFileSync(resolve(repoRoot, 'catalog/drawings.json'), 'utf8'));
    assert.equal(media.schemaVersion, 2);
    assert.equal(media.printSessions.length, 3);
    assert.equal(media.models.length, 10);
    const all = [...media.drawings, ...media.models, ...media.printSessions];
    assert.equal(new Set(all.map(item => item.id)).size, all.length);
    assert.equal(media.drawings.length, 26);
    assert.equal(media.drawings.filter(item => item.status === 'current').length, 20);
    assert.equal(media.drawings.filter(item => item.status === 'historical').length, 6);
    assert.equal(media.drawings.filter(item => item.status === 'reference').length, 0);
    for (const item of media.drawings) {
      assert.ok(['current', 'historical', 'reference'].includes(item.status));
      assert.ok(item.version);
      assert.ok(fs.existsSync(resolve(repoRoot, item.file)), `missing drawing ${item.file}`);
      assert.ok(fs.existsSync(resolve(repoRoot, item.preview)), `missing preview ${item.preview}`);
    }
    for (const item of media.models) {
      assert.ok(['current', 'historical', 'reference'].includes(item.status));
      assert.ok(item.version);
      assert.ok(fs.existsSync(resolve(repoRoot, item.file)), `missing model ${item.file}`);
      assert.ok(fs.existsSync(resolve(repoRoot, item.poster)), `missing poster ${item.poster}`);
    }
    for (const item of media.printSessions) {
      assert.equal(item.status, 'current');
      assert.equal(item.version, '0.7.4');
      assert.ok(fs.existsSync(resolve(repoRoot, item.file)), `missing print session ${item.file}`);
      assert.ok(fs.existsSync(resolve(repoRoot, item.preview)), `missing print session preview ${item.preview}`);
    }
  });

  it('catalogues every working visual artifact outside component images and archive', () => {
    const media = JSON.parse(fs.readFileSync(resolve(repoRoot, 'catalog/drawings.json'), 'utf8'));
    const referenced = new Set();
    for (const item of media.drawings) {
      referenced.add(item.file.replaceAll('\\', '/'));
      referenced.add(item.preview.replaceAll('\\', '/'));
    }
    for (const item of media.models) {
      referenced.add(item.file.replaceAll('\\', '/'));
      referenced.add(item.poster.replaceAll('\\', '/'));
    }
    for (const item of media.printSessions) {
      referenced.add(item.file.replaceAll('\\', '/'));
      referenced.add(item.preview.replaceAll('\\', '/'));
    }
    const allowedGeneratedCopies = new Set([
      'android/crucian-control/app/src/main/res/drawable-nodpi/ic_crucian_launcher.png',
    ]);
    const extensions = new Set(['.png', '.svg', '.glb', '.jpg', '.jpeg']);
    const found = [];
    function walk(directory) {
      for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
        const absolute = resolve(directory, entry.name);
        const relative = absolute.slice(repoRoot.length + 1).replaceAll('\\', '/');
        if (entry.isDirectory()) {
          if (relative === 'catalog/images' || relative.startsWith('catalog/images/') || relative === 'archive' || relative.startsWith('archive/')) continue;
          walk(absolute);
        } else if (extensions.has(entry.name.slice(entry.name.lastIndexOf('.')).toLowerCase())) {
          found.push(relative);
        }
      }
    }
    walk(repoRoot);
    const uncatalogued = found.filter(file => !referenced.has(file) && !allowedGeneratedCopies.has(file));
    assert.deepEqual(uncatalogued, []);
  });
});
