/* Политика рабочего каталога v0.7.5: только current и обязательные ID-выноски. §catalog */
import { spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const readJson = path => JSON.parse(fs.readFileSync(resolve(repoRoot, path), 'utf8'));
const currentVersion = fs.readFileSync(resolve(repoRoot, 'VERSION.txt'), 'utf8').trim();

describe('project catalog', () => {
  it('matches its JSON sources and generated callout images', () => {
    const render = spawnSync(process.execPath, ['scripts/runPython.mjs', 'mechanical/render_catalog_part_callouts_v075.py', '--check'], {
      cwd: repoRoot,
      encoding: 'utf8',
    });
    assert.equal(render.status, 0, render.stderr || render.stdout);

    const catalog = spawnSync(process.execPath, ['scripts/generateComponentCatalog.mjs', '--check'], {
      cwd: repoRoot,
      encoding: 'utf8',
    });
    assert.equal(catalog.status, 0, catalog.stderr || catalog.stdout);
  });

  it('uses continuous component IDs and one selected climate module', () => {
    const source = readJson('catalog/components.json');
    const ids = source.components.map(item => item.id).sort();
    assert.equal(ids.length, 25);
    assert.deepEqual(ids, Array.from({ length: 25 }, (_, index) => String(index + 1).padStart(3, '0')));
    assert.equal(source.components.filter(item => item.name.includes('AHT20 + BMP280')).length, 1);
  });

  it('publishes only the current version and never historical v0.5 cards', () => {
    assert.equal(currentVersion, '0.7.5');
    const media = readJson('catalog/drawings.json');
    assert.equal(media.schemaVersion, 3);
    assert.equal(media.catalogPolicy.visibility, 'current-only');
    assert.equal(media.catalogPolicy.currentVersion, currentVersion);
    assert.equal(media.catalogPolicy.partIdCallouts, 'required-for-all-drawings-and-models-except-print-layouts');
    assert.equal(media.catalogPolicy.sourceDrawingsRemainClean, true);

    const all = [...media.drawings, ...media.models, ...media.printSessions];
    assert.equal(new Set(all.map(item => item.id)).size, all.length);
    assert.ok(all.length > 0);
    assert.equal(all.every(item => item.status === 'current'), true);
    assert.equal(all.every(item => item.version === currentVersion), true);
    assert.equal(all.some(item => item.version === '0.5' || item.status === 'historical'), false);

    const forbidden = [
      'flagpole_finial_v0_5_assembly.glb',
      'flagpole_finial_v0_5_print_layout_PETG.glb',
      'flagpole_finial_v0_5_print_layout_TPU.glb',
      'Общий вид сборки v0.5 — интерактивно',
      'Раскладка деталей PETG v0.5 — интерактивно',
      'Раскладка TPU v0.5 — интерактивно, историческая',
    ];
    const jsonText = JSON.stringify(media);
    const html = fs.readFileSync(resolve(repoRoot, 'catalog/catalog.html'), 'utf8');
    for (const value of forbidden) {
      assert.doesNotMatch(jsonText, new RegExp(value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
      assert.doesNotMatch(html, new RegExp(value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
    }
    assert.doesNotMatch(html, /история · v0\.5|class="[^"]*historical/);
  });

  it('requires callouts on every non-print drawing and model', () => {
    const media = readJson('catalog/drawings.json');
    const registry = readJson('mechanical/part_id_registry_v06.json');
    const components = readJson('catalog/components.json');
    const allowedIds = new Set([
      ...components.components.map(item => item.id),
      ...Object.values(registry.groups).flat().map(item => item.id),
    ]);

    for (const item of media.drawings) {
      assert.ok(fs.existsSync(resolve(repoRoot, item.file)), `missing drawing ${item.file}`);
      assert.ok(fs.existsSync(resolve(repoRoot, item.preview)), `missing preview ${item.preview}`);
      if (item.kind === 'print-layout') {
        assert.equal(item.calloutMode, 'exempt');
        assert.ok(item.calloutExemptReason);
        assert.equal(item.callouts, undefined);
        assert.equal(item.annotatedPreview, undefined);
      } else if (item.calloutMode === 'embedded') {
        assert.ok(item.partIds.length > 0);
        assert.equal(item.partIds.every(id => allowedIds.has(id)), true);
      } else {
        assert.equal(item.calloutMode, 'overlay');
        assert.ok(item.callouts.length > 0);
        assert.ok(fs.existsSync(resolve(repoRoot, item.annotatedPreview)), `missing annotated drawing ${item.annotatedPreview}`);
        for (const callout of item.callouts) {
          assert.ok(allowedIds.has(callout.id), `unknown callout ${callout.id}`);
          assert.equal(callout.target.length, 2);
          assert.equal(callout.labelPosition.length, 2);
        }
      }
    }

    for (const item of media.models) {
      assert.ok(fs.existsSync(resolve(repoRoot, item.file)), `missing model ${item.file}`);
      assert.ok(fs.existsSync(resolve(repoRoot, item.poster)), `missing poster ${item.poster}`);
      if (item.kind === 'print-layout') {
        assert.equal(item.calloutMode, 'exempt');
        assert.ok(item.calloutExemptReason);
        assert.equal(item.callouts, undefined);
      } else {
        assert.equal(item.calloutMode, 'hotspots');
        assert.ok(item.callouts.length > 0);
        for (const callout of item.callouts) {
          assert.ok(allowedIds.has(callout.id), `unknown hotspot ${callout.id}`);
          assert.equal(callout.position.length, 3);
          assert.equal(callout.normal.length, 3);
        }
      }
    }
  });

  it('renders current-only wording, annotated drawings and 3D hotspots', () => {
    const html = fs.readFileSync(resolve(repoRoot, 'catalog/catalog.html'), 'utf8');
    for (const heading of ['ID', 'Картинка', 'Возможные названия компонента', 'Зачем он нужен', 'Описание или покупка']) {
      assert.match(html, new RegExp(`<th>${heading}</th>`));
    }
    assert.match(html, /только актуальных чертежей\/3D версии v0\.7\.5/i);
    assert.match(html, /catalog\/annotated\/101_electronics_wiring_diagram_A4_ids\.png/);
    assert.match(html, /class="model-hotspot"/);
    assert.match(html, /slot="hotspot-210-/);
    assert.match(html, /#petg-5/);
    assert.match(html, /Показанные ID/);
    assert.match(html, /раскладки печати намеренно не содержат выносок/i);
    assert.match(html, /model-viewer\/4\.2\.0\/model-viewer\.min\.js/);
    assert.match(html, /copyHotspots/);
    assert.match(html, /Компоновка электроники v0\.7\.5 — интерактивно/);
    assert.match(html, /одна поднятая крышка/i);
    assert.doesNotMatch(html, /актуально · v0\.7\.4/);
  });

  it('keeps print layouts clean in both 2D and 3D', () => {
    const media = readJson('catalog/drawings.json');
    const drawingLayouts = media.drawings.filter(item => item.kind === 'print-layout');
    const modelLayouts = media.models.filter(item => item.kind === 'print-layout');
    const printSessions = media.printSessions;
    assert.equal(drawingLayouts.length, 3);
    assert.equal(modelLayouts.length, 3);
    assert.equal(printSessions.length, 3);
    assert.equal([...drawingLayouts, ...modelLayouts, ...printSessions].every(item => item.calloutMode === 'exempt' && !item.callouts && !item.partIds && !item.annotatedPreview), true);
    assert.equal(drawingLayouts.every(item => !/_ids\.png$/i.test(item.preview)), true);
  });

  it('contains one canonical service lid in the electronics-layout generator', () => {
    const source = fs.readFileSync(resolve(repoRoot, 'mechanical/generate_models_v06.py'), 'utf8');
    const block = source.match(/electronics_names=\{[\s\S]*?electronics_path=/)?.[0] ?? '';
    assert.ok(block, 'electronics layout block not found');
    assert.doesNotMatch(block, /'PETG_service_lid'\s*,[\s\S]*electronics_scene=\{/);
    assert.doesNotMatch(block, /PETG_service_lid_raised/);
    assert.equal((block.match(/electronics_scene\['PETG_service_lid'\]/g) ?? []).length, 1);
  });
});
