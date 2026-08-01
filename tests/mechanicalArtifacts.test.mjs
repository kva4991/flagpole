import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const root = process.cwd();
const required = [
  'mechanical/generate_models_v06.py',
  'mechanical/flagpole_finial_v0_6_assembly.glb',
  'mechanical/flagpole_finial_v0_6_exploded.glb',
  'mechanical/flagpole_finial_v0_6_print_layout_PETG.glb',
  'mechanical/flagpole_finial_v0_6_print_layout_TPU95.glb',
  'mechanical/flagpole_finial_v0_6_print_layout_TPU85.glb',
  'mechanical/test_coupons_v06/PETG_M4_captive_nut_trap_coupon.stl',
  'mechanical/test_coupons_v06/PETG_drill_skin_0.6_0.8_1.0_coupon.stl',
  'flag_with_attachment_loops_full_size_300x250.svg',
  'flag_attachment_loop_pattern_A4_1to1.svg',
];

test('v0.6 mechanical sources and requested artifacts exist', () => {
  for (const file of required) {
    assert.ok(fs.existsSync(path.join(root, file)), `missing ${file}`);
  }
});

test('mechanical generator includes captive nuts, sensor pocket and four loop references', () => {
  const source = fs.readFileSync(path.join(root, 'mechanical/generate_models_v06.py'), 'utf8');
  assert.match(source, /captive_nut/i);
  assert.match(source, /environment_sensor_pocket/i);
  assert.match(source, /REF_flag_attachment_loop_\{loop_index\}/);
  assert.match(source, /REF_flag_attachment_loop_\{index\}/);
  assert.match(source, /start=1/);
});

test('flag loop documentation uses shaft gap in length formula', () => {
  const document = fs.readFileSync(path.join(root, 'mechanical/docs/FLAG_ATTACHMENT_LOOPS_RU.md'), 'utf8');
  assert.match(document, /L = 2 × G \+ π × Dштока/);
});
