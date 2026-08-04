import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const root = process.cwd();
const supersededGeneratedArtifacts = [
  'archive/legacy_v02_reference',
  'archive/legacy_v073_reference',
  'mechanical/stl_petg',
  'mechanical/stl_tpu',
  'mechanical/test_coupons',
  'mechanical/build123d_experimental_v076',
  'mechanical/flagpole_finial_v0_5_assembly.glb',
  'mechanical/flagpole_finial_v0_5_print_layout_PETG.glb',
  'mechanical/flagpole_finial_v0_5_print_layout_TPU.glb',
  'mechanical/generate_models_v05.py',
  'mechanical/generate_build123d_experimental_v076.py',
  'mechanical/generate_detail_diagrams_v074.py',
  'mechanical/generate_hermeticity_diagram_v074.py',
];

test('superseded generated CAD artifacts stay removed', () => {
  for (const relativePath of supersededGeneratedArtifacts) {
    assert.equal(fs.existsSync(path.join(root, relativePath)), false, `obsolete artifact returned: ${relativePath}`);
  }
});

const required = [
  'mechanical/generate_models_v06.py',
  'mechanical/generate_build123d_canonical_v076.py',
  'mechanical/build123d_v076/BUILD123D_CANONICAL_REPORT.json',
  'mechanical/requirements.txt',
  'mechanical/render_catalog_part_callouts_v075.py',
  'mechanical/validate_catalog_model_semantics_v075.py',
  'mechanical/flagpole_finial_v0_6_assembly.glb',
  'mechanical/flagpole_finial_v0_6_exploded.glb',
  'mechanical/flagpole_finial_v0_6_exploded_with_fasteners.glb',
  'mechanical/flagpole_finial_v0_6_flag_power_route.glb',
  'mechanical/flagpole_finial_v0_6_electronics_layout.glb',
  'mechanical/flagpole_finial_v0_6_print_layout_PETG.glb',
  'mechanical/flagpole_finial_v0_6_print_layout_TPU95.glb',
  'mechanical/flagpole_finial_v0_6_print_layout_TPU85.glb',
  'mechanical/stl_petg_v06/electronics_carrier_open_side_up.stl',
  'mechanical/stl_petg_v06/VEML7700_cradle_flat.stl',
  'mechanical/stl_tpu95_v06/flag_side_wire_guide_closed.stl',
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
  const source = fs.readFileSync(path.join(root, 'mechanical/generate_build123d_canonical_v076.py'), 'utf8');
  assert.match(source, /native build123d/i);
  assert.match(source, /def rotor_half/);
  assert.match(source, /hex_y\(PARAM\.m4_hex/);
  assert.match(source, /hex_z\(PARAM\.m3_hex/);
  assert.match(source, /def closed_wire_guide/);
  assert.match(source, /Two completely closed through channels/);
  assert.match(source, /def environment_pocket/);
  assert.match(source, /def top_loaded_m3_well/);
  assert.match(source, /Blind 5 mm socket/);
  assert.match(source, /cyl_z\(5\.0, 18\.0, \(x, y, 42\.2\)\)/);
  assert.match(source, /gasket_screw_overlap_mm3/);
  assert.match(source, /Continuous inner sealing shelf/);
  assert.match(source, /carrier_opening_clearance_y_mm/);
  assert.match(source, /carrier_outside_opening_mm3/);
  assert.doesNotMatch(source, /mouth_y\s*=/);
  assert.doesNotMatch(source, /Climate-pocket nuts load from the outside/);
  assert.match(source, /def electronics_carrier/);
  assert.match(source, /def photo_tunnel/);
  assert.doesNotMatch(source, /load_source_mesh|SOURCE_MESH_DIR|source_meshes_v073/);
  const report = JSON.parse(fs.readFileSync(path.join(root, 'mechanical/build123d_v076/BUILD123D_CANONICAL_REPORT.json'), 'utf8'));
  assert.equal(report.nativeBuild123dNodes, 23);
  assert.equal(report.legacyMeshNodes, 0);
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
  const report = JSON.parse(fs.readFileSync(path.join(root, 'mechanical/build123d_v076/BUILD123D_CANONICAL_REPORT.json'), 'utf8'));
  assert.deepEqual(report.guideStartMm, [15.2, -17.2, 4.8]);
  assert.deepEqual(report.guideEndMm, [29.2, -17.2, -5]);
  assert.ok(Math.abs(report.guideAngleDownDeg - 35) < 0.1);
  assert.match(report.wireGuide, /closed twin through-channels/);
  assert.match(report.spokeBore, /opens through flag-side end face/);
  assert.deepEqual(report.environmentDripLipMm, { outerDiameter: 22, innerDiameter: 20.8, height: 1, drainGaps: 4 });
  assert.match(report.vemlCradleCentre, /no unjustified central through-hole/);
  assert.equal(report.electronicsEnclosure.centreXmm, -60);
  assert.deepEqual(report.electronicsEnclosure.outerMm, [72, 42, 40]);
  assert.deepEqual(report.electronicsEnclosure.lidOuterMm, [74, 44, 3.6]);
  assert.ok(report.electronicsEnclosure.towerToLidClearanceMm >= 0.35);
  assert.equal(report.electronicsEnclosure.lidCollisionVolumeMm3, 0);
  assert.equal(report.electronicsEnclosure.locatingSkirtClearancePerSideMm, 0.4);
  assert.equal(report.electronicsEnclosure.gasketCompressionPercent, 25);
  assert.match(report.electronicsEnclosure.seal, /continuous inner shelf and lid groove/);
  assert.match(report.electronicsEnclosure.seal, /screw holes stay outside the dry gasket contour/);
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
