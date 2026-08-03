import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const root = process.cwd();
const required = [
  'mechanical/generate_models_v06.py',
  'mechanical/requirements.txt',
  'mechanical/render_catalog_part_callouts_v075.py',
  'mechanical/validate_catalog_model_semantics_v075.py',
  'mechanical/flagpole_finial_v0_6_assembly.glb',
  'mechanical/flagpole_finial_v0_6_exploded.glb',
  'mechanical/flagpole_finial_v0_6_flag_power_route.glb',
  'mechanical/flagpole_finial_v0_6_electronics_layout.glb',
  'mechanical/flagpole_finial_v0_6_print_layout_PETG.glb',
  'mechanical/flagpole_finial_v0_6_print_layout_TPU95.glb',
  'mechanical/flagpole_finial_v0_6_print_layout_TPU85.glb',
  'mechanical/stl_petg_v06/electronics_carrier_open_side_up.stl',
  'mechanical/stl_petg_v06/VEML7700_cradle_flat.stl',
  'mechanical/stl_tpu95_v06/flag_side_wire_guide_slit_up.stl',
  'mechanical/test_coupons_v06/PETG_M4_captive_nut_trap_coupon.stl',
  'mechanical/test_coupons_v06/PETG_M3_captive_nut_trap_coupon.stl',
  'mechanical/test_coupons_v06/PETG_twin_wire_rail_4.2x2.5_coupon.stl',
  'mechanical/test_coupons_v06/PETG_photo_tunnel_15_18_comparison_coupon.stl',
  'flag_with_attachment_loops_full_size_300x250.svg',
  'flag_attachment_loop_pattern_A4_1to1.svg',
  'mechanical/flag_power_cable_route_A4_landscape.svg',
  'mechanical/fastener_captive_nut_map_A4_landscape.svg',
  'mechanical/electronics_layout_A4_landscape.svg',
  'mechanical/current_longitudinal_section_v075.svg',
  'mechanical/generate_reference_diagrams_v06.py',
  'mechanical/generate_detail_diagrams_v075.py',
  'mechanical/generate_hermeticity_diagram_v075.py',
  'electronics/generate_electronics_diagrams_v075.py',
  'mechanical/validate_models_v06.py',
  'mechanical/layout_packing.py',
  'mechanical/CALLOUT_LAYOUT_REPORT_V076.json',
];

test('current v0.7.6 mechanical sources and requested artifacts exist', () => {
  for (const file of required) assert.ok(fs.existsSync(path.join(root, file)), `missing ${file}`);
});

test('current generator is parametric and includes all requested features', () => {
  const source = fs.readFileSync(path.join(root, 'mechanical/generate_models_v06.py'), 'utf8');
  assert.match(source, /CURRENT_VERSION = "0\.7\.6"/);
  assert.match(source, /m4_nut_pocket_across_flats/);
  assert.match(source, /m3_nut_pocket_across_flats/);
  assert.match(source, /flag_side_wire_guide_sdf/);
  assert.match(source, /environment_membrane_open_area_mm2/);
  assert.match(source, /electronics_carrier_sdf/);
  assert.match(source, /photo_glue_groove/);
  assert.match(source, /flag_loop_top_offsets/);
  assert.doesNotMatch(source, /load_source_mesh|SOURCE_MESH_DIR|source_meshes_v073/);
});

test('electronics service view creates exactly one canonical lid', () => {
  const source = fs.readFileSync(path.join(root, 'mechanical/generate_models_v06.py'), 'utf8');
  const block = source.match(/electronics_names=\{[\s\S]*?electronics_path=/)?.[0] ?? '';
  assert.ok(block);
  assert.doesNotMatch(block, /PETG_service_lid_raised/);
  assert.equal((block.match(/electronics_scene\['PETG_service_lid'\]/g) ?? []).length, 1);
  const namesSet = block.match(/electronics_names=\{([\s\S]*?)\}/)?.[1] ?? '';
  assert.doesNotMatch(namesSet, /PETG_service_lid/);
});

test('flag cable route reaches the owner point below fasteners through the angled guide', () => {
  const diagnostics = JSON.parse(fs.readFileSync(path.join(root, 'mechanical/model_parameters_and_diagnostics_v06.json'), 'utf8'));
  const p = diagnostics.parameters_mm;
  assert.equal(diagnostics.version.startsWith('0.7.6'), true);
  assert.ok(p.flag_cable_center_z < p.spoke_center_z);
  assert.equal(p.twin_wire_clear_width, 4.2);
  assert.equal(p.wire_rail_height, 2.5);
  assert.ok(Math.abs(diagnostics.derived_mm.flag_side_guide_angle_down_deg - 35) < 0.1);
  assert.deepEqual(p.flag_side_guide_start, [58.0, -16.2, 15.0]);
  assert.deepEqual(p.flag_side_guide_end, [72.0, -16.2, 5.2]);
  const document = fs.readFileSync(path.join(root, 'mechanical/docs/FLAG_POWER_CABLE_ROUTE_RU.md'), 'utf8');
  assert.match(document, /вход.*единственн/i);
  assert.match(document, /34,99°/);
  assert.match(document, /#tpu95-3/);
  assert.match(document, /#tpu95-4/);
});

test('flag loop datum, membrane, tunnel and captive nuts match v0.7.6', () => {
  const diagnostics = JSON.parse(fs.readFileSync(path.join(root, 'mechanical/model_parameters_and_diagnostics_v06.json'), 'utf8'));
  assert.deepEqual(diagnostics.derived_mm.flag_loop_top_offsets.map(v => Math.round(v * 100) / 100), [45, 106.67, 168.33, 230]);
  assert.ok(Math.abs(diagnostics.derived_mm.environment_membrane_open_area_mm2 - 21.9911) < 0.01);
  assert.equal(diagnostics.parameters_mm.env_membrane_disc_diameter, 20);
  assert.equal(diagnostics.parameters_mm.env_membrane_active_diameter, 10);
  assert.equal(diagnostics.parameters_mm.env_vent_hole_count, 7);
  assert.equal(diagnostics.parameters_mm.photo_tunnel_height, 15);
  assert.equal(diagnostics.parameters_mm.m4_nut_pocket_across_flats, 7.3);
  assert.equal(diagnostics.parameters_mm.m3_nut_pocket_across_flats, 5.8);
});

test('part registry uses unique IDs and current STL files', () => {
  const registry = JSON.parse(fs.readFileSync(path.join(root, 'mechanical/part_id_registry_v06.json'), 'utf8'));
  const items = Object.values(registry.groups).flat();
  const ids = items.map(item => item.id);
  assert.equal(items.length, 23);
  assert.equal(new Set(ids).size, ids.length);
  assert.ok(ids.includes('#petg-9'));
  assert.ok(ids.includes('#petg-10'));
  assert.ok(ids.includes('#tpu95-10'));
  assert.equal(ids.includes('#tpu85-4'), false);
  for (const item of items) assert.ok(fs.existsSync(path.join(root, item.stl)), `missing STL for ${item.id}: ${item.stl}`);
});


test('callout renderer is cross-platform and does not depend on host fonts', () => {
  const source = fs.readFileSync(path.join(root, 'mechanical/render_catalog_part_callouts_v075.py'), 'utf8');
  assert.match(source, /GLYPHS:/);
  assert.match(source, /ImageChops\.difference/);
  assert.doesNotMatch(source, /ImageFont\.truetype|Windows\\Fonts|DejaVuSans/);
  assert.ok(fs.existsSync(path.join(root, 'scripts/runPython.mjs')));
});

test('all current SVG generators use the portable resvg dependency', () => {
  const generators = [
    'mechanical/generate_reference_diagrams_v06.py',
    'mechanical/generate_detail_diagrams_v075.py',
    'mechanical/generate_hermeticity_diagram_v075.py',
    'electronics/generate_electronics_diagrams_v075.py',
  ];
  const requirements = fs.readFileSync(path.join(root, 'mechanical/requirements.txt'), 'utf8');
  for (const generator of generators) {
    const source = fs.readFileSync(path.join(root, generator), 'utf8');
    assert.match(source, /from resvg_py import svg_to_bytes/);
    assert.doesNotMatch(source, /import cairosvg/);
  }
  assert.match(requirements, /^resvg-py==/m);
  assert.match(requirements, /^Pillow==/m);
});

test('flag loop documentation keeps the shaft-gap formula and current datum', () => {
  const document = fs.readFileSync(path.join(root, 'mechanical/docs/FLAG_ATTACHMENT_LOOPS_RU.md'), 'utf8');
  assert.match(document, /L = 2 × G \+ π × Dштока/);
  assert.match(document, /10 мм ниже нижней кромки навершия/);
});
