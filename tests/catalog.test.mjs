/* Политика рабочего каталога v0.7.6: только current и обязательные ID-выноски. §catalog */
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
  it('matches its JSON sources and generated callout images', t => {
    const executionRoot = process.env.FLAGPOLE_EXECUTION_ROOT ? resolve(process.env.FLAGPOLE_EXECUTION_ROOT) : null;
    const protectedWindowsCopy = process.platform !== 'win32' || (executionRoot && repoRoot.toLowerCase().startsWith(`${executionRoot.toLowerCase()}\\`));
    if (protectedWindowsCopy) {
      const render = spawnSync(process.execPath, ['scripts/runPython.mjs', 'mechanical/render_catalog_part_callouts_v075.py', '--check'], {
        cwd: repoRoot,
        encoding: 'utf8',
        env: { ...process.env, PYTHONUTF8: '1', PYTHONIOENCODING: 'utf-8' },
      });
      assert.equal(render.status, 0, render.stderr || render.stdout);
    } else {
      t.diagnostic('Python callout check deferred to the synchronized pesochnica worktree.');
    }

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

  it('keeps physical dimensions in one registry and selects the 6806 bearing candidate', () => {
    const source = readJson('catalog/components.json');
    const physical = readJson('catalog/physical-components.json');
    const componentIds = source.components.map(item => item.id).sort();
    const physicalIds = physical.components.map(item => item.id).sort();
    const bearing = physical.components.find(item => item.id === '008');
    const pole = physical.components.find(item => item.id === '015');
    const wire = physical.components.find(item => item.id === '022');
    const valuesFor = item => new Map(item.measurements.map(measurement => [measurement.key, measurement.value]));

    assert.deepEqual(physicalIds, componentIds);
    assert.equal(physical.tag, '§physicalcomponents1');
    assert.equal(bearing.selection, 'selected-candidate');
    assert.equal(valuesFor(bearing).get('bore-diameter'), '30');
    assert.equal(valuesFor(bearing).get('outer-diameter'), '42');
    assert.equal(valuesFor(bearing).get('width'), '7');
    assert.equal(valuesFor(pole).get('pole-outer-diameter'), '24,9');
    assert.equal(valuesFor(pole).get('pole-inner-diameter'), '24,3');
    assert.equal(valuesFor(pole).get('target-segment-inner-diameter'), '24,3');
    assert.equal(valuesFor(pole).get('calculated-wall-thickness'), '0,3');
    assert.equal(valuesFor(pole).has('pole-ovality'), false);
    assert.equal(valuesFor(wire).get('external-wire-diameter'), '2');
    assert.equal(valuesFor(wire).get('internal-wire-pair-width'), '4');
    assert.match(source.components.find(item => item.id === '008').name, /6806-2RS/);
    assert.doesNotMatch(JSON.stringify(source.components.find(item => item.id === '015')), /24,9 мм|24,3 мм|0,3 мм/);
  });

  it('publishes a stable anchor for every physical component and links every model rationale', () => {
    const source = readJson('catalog/components.json');
    const media = readJson('catalog/drawings.json');
    const html = fs.readFileSync(resolve(repoRoot, 'catalog/catalog.html'), 'utf8');

    for (const item of source.components) assert.match(html, new RegExp(`id="component-${item.id}"`));
    for (const item of media.models) {
      const description = fs.readFileSync(resolve(repoRoot, item.descriptionFile), 'utf8');
      assert.match(description, /§physicalcomponents1/);
      assert.match(description, /\.\.\/catalog\.html#component-\d{3}/);
    }
  });

  it('publishes the source-only PETG 6806 adapter draft without generated artifacts', () => {
    const media = readJson('catalog/drawings.json');
    const draftPath = 'mechanical/cad_drafts/petg_6806_adapter_v076.json';
    const draft = readJson(draftPath);
    const html = fs.readFileSync(resolve(repoRoot, 'catalog/catalog.html'), 'utf8');
    const dimensions = new Map(draft.finalPart.dimensions.map(item => [item.key, item.value]));
    const couponIds = draft.couponSets.flatMap(set => set.variants.map(item => item.id));

    assert.equal(media.catalogPolicy.cadDraftSources.includes(draftPath), true);
    assert.equal(draft.id, '401');
    assert.equal(draft.status, 'source-only-not-generated');
    assert.equal(draft.material, 'PETG');
    assert.equal(draft.finalPart.partId, '#petg-11');
    assert.equal(draft.finalPart.quantity, 2);
    assert.equal(dimensions.get('pole-bore-diameter'), 25.2);
    assert.equal(dimensions.get('bearing-seat-diameter'), 30.0);
    assert.equal(dimensions.get('axial-width'), 7.0);
    assert.equal(dimensions.get('nominal-radial-wall'), 2.4);
    assert.deepEqual(couponIds, ['40101', '40102', '40103', '40104', '40105', '40106']);
    for (const output of draft.plannedOutputs) assert.equal(fs.existsSync(resolve(repoRoot, output)), false, `${output} must not exist before generation approval`);
    assert.match(fs.readFileSync(resolve(repoRoot, draft.sourceFile), 'utf8'), /def adapter_ring\(|--generate-coupons|--generate-final/);
    assert.match(html, /id="cad-draft-401"/);
    assert.match(html, /CAD-заготовки без генерации/);
    assert.match(html, /#40101/);
    assert.match(html, /STL, STEP, GLB и изображение отсутствуют намеренно/);
  });

  it('publishes the source-only flexible lower-pole strain relief with two wire channels', () => {
    const media = readJson('catalog/drawings.json');
    const draftPath = 'mechanical/cad_drafts/tpu85_lower_pole_strain_relief_v076.json';
    const draft = readJson(draftPath);
    const html = fs.readFileSync(resolve(repoRoot, 'catalog/catalog.html'), 'utf8');
    const dimensions = new Map(draft.finalPart.dimensions.map(item => [item.key, item.value]));
    const couponIds = draft.couponSets.flatMap(set => set.variants.map(item => item.id));

    assert.equal(media.catalogPolicy.cadDraftSources.includes(draftPath), true);
    assert.equal(draft.id, '402');
    assert.equal(draft.draftType, 'flexible-cable-strain-relief');
    assert.equal(draft.tag, '§lowercablestrain1');
    assert.equal(draft.status, 'source-only-not-generated');
    assert.equal(draft.material, 'TPU 85A');
    assert.equal(draft.finalPart.partId, '#tpu85-4');
    assert.equal(dimensions.get('wire-channel-diameter'), 2.0);
    assert.equal(dimensions.get('wire-channel-pair-span'), 4.0);
    assert.equal(dimensions.get('seat-core-diameter'), 24.0);
    assert.equal(dimensions.get('retention-rib-outer-diameter'), 24.7);
    assert.equal(dimensions.get('retention-rib-count'), 6);
    assert.deepEqual(couponIds, ['40201', '40202', '40203', '40204', '40205', '40206']);
    for (const output of draft.plannedOutputs) assert.equal(fs.existsSync(resolve(repoRoot, output)), false, `${output} must not exist before generation approval`);
    const source = fs.readFileSync(resolve(repoRoot, draft.sourceFile), 'utf8');
    assert.match(source, /def paired_wire_coupon\(|def strain_relief\(/);
    assert.match(source, /--generate-coupons|--generate-final/);
    assert.match(html, /id="cad-draft-402"/);
    assert.match(html, /2 × Ø2 мм/);
    assert.match(html, /6 рёбер · Ø24,7 мм/);
    assert.match(html, /#40204/);
  });

  it('publishes only the current version and never historical v0.5 cards', () => {
    assert.equal(currentVersion, '0.7.6');
    const media = readJson('catalog/drawings.json');
    assert.equal(media.schemaVersion, 6);
    assert.equal(media.catalogPolicy.visibility, 'current-only');
    assert.equal(media.catalogPolicy.currentVersion, currentVersion);
    assert.equal(media.catalogPolicy.partIdCallouts, 'required-for-all-drawings-and-models-except-print-layouts');
    assert.equal(media.catalogPolicy.sourceDrawingsRemainClean, true);
    assert.equal(media.catalogPolicy.physicalMeasurements, 'catalog/physical-components.json');
    assert.equal(media.catalogPolicy.componentPermalinks, 'catalog/catalog.html#component-<ID>');
    assert.deepEqual(media.catalogPolicy.cadDraftSources, [
      'mechanical/cad_drafts/petg_6806_adapter_v076.json',
      'mechanical/cad_drafts/tpu85_lower_pole_strain_relief_v076.json',
    ]);

    const canonical = [...media.drawings, ...media.models, ...media.printSessions];
    const all = [...canonical, ...media.experimentalModels];
    assert.equal(new Set(all.map(item => item.id)).size, all.length);
    assert.ok(all.length > 0);
    assert.equal(canonical.every(item => item.status === 'current'), true);
    assert.equal(media.experimentalModels.every(item => item.status === 'experimental'), true);
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
    const featureRegistry = readJson('mechanical/feature_id_registry_v076.json');
    const components = readJson('catalog/components.json');
    const allowedIds = new Set([
      ...components.components.map(item => item.id),
      ...Object.values(registry.groups).flat().map(item => item.id),
      ...featureRegistry.features.map(item => item.id),
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

    for (const item of media.experimentalModels) {
      assert.ok(fs.existsSync(resolve(repoRoot, item.file)), `missing experimental model ${item.file}`);
      assert.ok(fs.existsSync(resolve(repoRoot, item.poster)), `missing experimental poster ${item.poster}`);
      assert.equal(item.calloutMode, 'hotspots');
      const source = media.models.find(model => model.id === item.calloutsFrom);
      assert.ok(source, `missing callout source ${item.calloutsFrom}`);
      assert.ok(source.callouts.length > 0);
    }
  });

  it('renders current-only wording, annotated drawings and 3D hotspots', () => {
    const html = fs.readFileSync(resolve(repoRoot, 'catalog/catalog.html'), 'utf8');
    for (const heading of ['ID', 'Картинка', 'Возможные названия компонента', 'Зачем он нужен', 'Описание или покупка']) {
      assert.match(html, new RegExp(`<th>${heading}</th>`));
    }
    assert.match(html, /только актуальных чертежей\/3D версии v0\.7\.6/i);
    assert.match(html, /catalog\/annotated\/101_electronics_wiring_diagram_A4_ids\.png/);
    assert.match(html, /class="model-hotspot"/);
    assert.match(html, /slot="hotspot-210-/);
    assert.match(html, /#petg-5/);
    assert.match(html, /Показанные ID/);
    assert.match(html, /раскладки печати намеренно не содержат выносок/i);
    assert.match(html, /model-viewer\/4\.2\.0\/model-viewer\.min\.js/);
    assert.match(html, /copyHotspots/);
    assert.match(html, /Компоновка электроники v0\.7\.6 — интерактивно/);
    assert.match(html, /одна поднятая крышка/i);
    assert.doesNotMatch(html, /актуально · v0\.7\.4/);
  });

  it('shows an automatically calculated file size for every image and model card', () => {
    const html = fs.readFileSync(resolve(repoRoot, 'catalog/catalog.html'), 'utf8');
    const media = readJson('catalog/drawings.json');
    const components = readJson('catalog/components.json');
    const componentImageCount = components.components.reduce((count, item) => count + 1 + (item.additionalImages?.length ?? 0), 0);
    const mediaCardCount = media.drawings.length + media.models.length + media.printSessions.length;

    assert.equal((html.match(/class="asset-size"/g) ?? []).length, componentImageCount);
    assert.equal((html.match(/class="asset-sizes"/g) ?? []).length, mediaCardCount);
    assert.match(html, /<strong>Постер:<\/strong> [\d,]+ (?:КБ|МБ)/);
    assert.match(html, /<strong>GLB:<\/strong> [\d,]+ МБ/);
    assert.match(html, /<strong>Миниатюра:<\/strong> [\d,]+ (?:КБ|МБ)/);
    assert.match(html, /<strong>Изображение с ID:<\/strong> [\d,]+ (?:КБ|МБ)/);
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
