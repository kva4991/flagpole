import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const root = process.cwd();
const required = [
  'mechanical/generate_models_v06.py',
  'mechanical/requirements.txt',
  'mechanical/flagpole_finial_v0_6_assembly.glb',
  'mechanical/flagpole_finial_v0_6_exploded.glb',
  'mechanical/flagpole_finial_v0_6_flag_power_route.glb',
  'mechanical/flagpole_finial_v0_6_print_layout_PETG.glb',
  'mechanical/flagpole_finial_v0_6_print_layout_TPU95.glb',
  'mechanical/flagpole_finial_v0_6_print_layout_TPU85.glb',
  'mechanical/test_coupons_v06/PETG_M4_captive_nut_trap_coupon.stl',
  'mechanical/test_coupons_v06/PETG_drill_skin_0.6_0.8_1.0_coupon.stl',
  'flag_with_attachment_loops_full_size_300x250.svg',
  'flag_attachment_loop_pattern_A4_1to1.svg',
  'mechanical/flag_power_cable_route_A4_landscape.svg',
  'mechanical/flag_power_cable_route_A4_landscape.png',
  'mechanical/docs/FLAG_POWER_CABLE_ROUTE_RU.md',
  'mechanical/part_id_registry_v06.json',
  'mechanical/part_id_table_v06.svg',
  'mechanical/part_id_table_v06.png',
  'mechanical/generate_reference_diagrams_v06.py',
  'mechanical/validate_models_v06.py',
];

test('v0.6 mechanical sources and requested artifacts exist', () => {
  for (const file of required) {
    assert.ok(fs.existsSync(path.join(root, file)), `missing ${file}`);
  }
});

test('mechanical generator includes captive nuts, sensor pocket, loops and external cable route', () => {
  const source = fs.readFileSync(path.join(root, 'mechanical/generate_models_v06.py'), 'utf8');
  assert.match(source, /captive_nut/i);
  assert.match(source, /environment_sensor_pocket/i);
  assert.match(source, /REF_flag_attachment_loop_\{loop_index\}/);
  assert.match(source, /REF_flag_attachment_loop_\{index\}/);
  assert.match(source, /external_cable_route_points/);
  assert.match(source, /REF_flag_power_cable_external_route/);
  assert.match(source, /start=1/);
});

test('flag cable route stays below spoke and enters beside electronics pod', () => {
  const diagnostics = JSON.parse(fs.readFileSync(path.join(root, 'mechanical/model_parameters_and_diagnostics_v06.json'), 'utf8'));
  const parameters = diagnostics.parameters_mm;
  assert.ok(parameters.flag_cable_center_z < parameters.spoke_center_z);
  assert.ok(Array.isArray(parameters.external_cable_route_points));
  assert.ok(parameters.external_cable_route_points.length >= 5);
  assert.equal(parameters.flag_cable_x_min, -18.0);
  assert.ok(Math.min(...parameters.external_cable_route_points.map(point => point[2])) < parameters.flag_cable_center_z);
  const document = fs.readFileSync(path.join(root, 'mechanical/docs/FLAG_POWER_CABLE_ROUTE_RU.md'), 'utf8');
  assert.match(document, /единственн.*герметизируем.*ввод/i);
  assert.match(document, /под спиц/i);
  assert.match(document, /#tpu95-3/);
  assert.match(document, /#tpu95-4/);
});

test('part registry uses unique stable IDs and existing STL files', () => {
  const registry = JSON.parse(fs.readFileSync(path.join(root, 'mechanical/part_id_registry_v06.json'), 'utf8'));
  const items = Object.values(registry.groups).flat();
  const ids = items.map(item => item.id);
  assert.equal(new Set(ids).size, ids.length);
  assert.ok(ids.every(id => /^#(?:petg|tpu95|tpu85)-\d+$/.test(id)));
  for (const item of items) {
    assert.ok(item.description, `missing description for ${item.id}`);
    assert.ok(Number.isInteger(item.quantity) && item.quantity > 0, `invalid quantity for ${item.id}`);
    assert.ok(fs.existsSync(path.join(root, item.stl)), `missing STL for ${item.id}: ${item.stl}`);
  }
});

test('reference diagram generator avoids a native Cairo dependency on Windows', () => {
  const source = fs.readFileSync(path.join(root, 'mechanical/generate_reference_diagrams_v06.py'), 'utf8');
  const requirements = fs.readFileSync(path.join(root, 'mechanical/requirements.txt'), 'utf8');
  assert.match(source, /from resvg_py import svg_to_bytes/);
  assert.doesNotMatch(source, /import cairosvg/);
  assert.match(requirements, /^resvg-py==/m);
});

test('flag loop documentation uses shaft gap in length formula', () => {
  const document = fs.readFileSync(path.join(root, 'mechanical/docs/FLAG_ATTACHMENT_LOOPS_RU.md'), 'utf8');
  assert.match(document, /L = 2 × G \+ π × Dштока/);
});
