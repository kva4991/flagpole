import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const root = process.cwd();

test('all three print layouts are compact, single-material and contain no backing geometry', () => {
  const diagnostics = JSON.parse(fs.readFileSync(path.join(root, 'mechanical/model_parameters_and_diagnostics_v06.json'), 'utf8'));
  const layouts = diagnostics.printLayouts;
  assert.ok(layouts && Object.keys(layouts).length === 3);
  const expected = {
    'flagpole_finial_v0_6_print_layout_PETG.glb': { minimum: 6, partCount: 10 },
    'flagpole_finial_v0_6_print_layout_TPU95.glb': { minimum: 5, partCount: 10 },
    'flagpole_finial_v0_6_print_layout_TPU85.glb': { minimum: 5, partCount: 3 },
  };
  for (const [file, expectation] of Object.entries(expected)) {
    const item = layouts[file];
    assert.ok(item, `missing diagnostics for ${file}`);
    assert.ok(item.usedWidthMm <= item.bedSizeMm - 2 * item.edgeReserveMm + 1e-6);
    assert.ok(item.usedDepthMm <= item.bedSizeMm - 2 * item.edgeReserveMm + 1e-6);
    assert.ok(item.minimumAabbClearanceMm >= expectation.minimum - 1e-6);
    assert.equal(item.partCount, expectation.partCount);
    assert.equal(item.items.length, expectation.partCount);
    assert.equal(item.containsCanonicalBackingGeometry, false);
    for (const part of item.items) assert.doesNotMatch(part.name, /backing|raft|brim|build[_ -]?plate/i);
  }
});

test('printing documentation does not present the service lid as a sacrificial PETG backing', () => {
  const document = fs.readFileSync(path.join(root, 'mechanical/docs/PRINTING_PETG_TPU_RU.md'), 'utf8');
  assert.match(document, /канонических PETG-подложек под TPU нет/i);
  assert.match(document, /#petg-5.*функциональн/i);
  assert.match(document, /brim.*raft.*слайсер/i);
  assert.doesNotMatch(document, /сервисные подложки или вспомогательные элементы/i);
});
