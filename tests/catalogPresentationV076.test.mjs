import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const root = process.cwd();
const media = JSON.parse(fs.readFileSync(path.join(root, 'catalog/drawings.json'), 'utf8'));
const identity = JSON.parse(fs.readFileSync(path.join(root, 'project_identity.json'), 'utf8'));
const html = fs.readFileSync(path.join(root, 'catalog/catalog.html'), 'utf8');

test('v0.7.6 uses clean media thumbnails and the requested public name', () => {
  assert.equal(identity.projectDisplayName, 'Super_pommels_and_flag');
  assert.equal(media.schemaVersion, 4);
  assert.equal(identity.bluetoothDeviceName, 'Crucian');
  assert.equal(media.catalogPolicy.thumbnailIdentifiers, 'hidden');
  assert.equal(media.catalogPolicy.fullscreenIdentifierToggle, true);
  assert.equal(media.catalogPolicy.labelPlacement, 'automatic-near-target');

  for (const item of media.drawings) {
    assert.ok(item.thumbnail, `missing clean thumbnail for drawing ${item.id}`);
    assert.ok(fs.existsSync(path.join(root, item.thumbnail)), `missing thumbnail ${item.thumbnail}`);
    assert.doesNotMatch(item.thumbnail, /catalog[\\/]annotated|_ids\.png$/i);
    if (item.calloutMode === 'overlay') assert.equal(item.thumbnail, item.preview);
  }
  assert.equal(media.drawings.find(item => item.id === '112').thumbnail, 'mechanical/preview_v06_exploded_PETG_TPU.png');
  assert.equal(media.drawings.find(item => item.id === '117').thumbnail, 'catalog/clean_document_thumbnail.svg');
  assert.match(html, /Проект Super_pommels_and_flag/);
  assert.doesNotMatch(html, /<img[^>]+src="[^"]*(?:catalog\/annotated|_ids\.png)/i);
  const previewRenderer = fs.readFileSync(path.join(root, 'mechanical/render_previews_v06.py'), 'utf8');
  assert.doesNotMatch(previewRenderer, /preview_v06_print_[^\n]+['"]#(?:petg|tpu)/i);
});

test('fullscreen viewer exposes an accessible ID visibility toggle next to close', () => {
  assert.match(html, /id="fullscreenToggleIds"/);
  assert.match(html, /class="fullscreen-controls"/);
  assert.match(html, /aria-pressed="true"/);
  assert.match(html, /setFullscreenIdsVisible/);
  assert.match(html, /ids-hidden/);
  assert.match(html, /fullscreenToggleIds\.hidden=!hasHotspots/);
  assert.match(html, /model-card \.viewer-shell>model-viewer \.model-hotspot\{display:none\}/);
  assert.match(html, /<svg[^>]+viewBox="0 0 24 24"/);
});

test('compact callout report exists and proves shorter resolved leaders', () => {
  const report = JSON.parse(fs.readFileSync(path.join(root, 'mechanical/CALLOUT_LAYOUT_REPORT_V076.json'), 'utf8'));
  assert.equal(report.version, '0.7.6');
  assert.ok(report.summary.calloutCount > 0);
  assert.ok(report.summary.resolvedMeanLeaderLengthNormalized < report.summary.legacyMeanLeaderLengthNormalized);
  assert.ok(Number.isInteger(report.summary.resolvedLeaderCrossings));
  assert.ok(report.summary.resolvedLeaderCrossings >= 0);
});
test('current public entry points do not present Crucian as the project name', () => {
  const paths = [
    'AGENTS.md', 'README.md', 'README.ru.md', 'docs/PROJECT_IDENTITY_RU.md',
    'catalog/catalog.html', 'PROJECT_MANIFEST.json',
  ];
  const legacyName = ['Cru', 'cian'].join('');
  const stale = new RegExp(`(?:Проект|проект|проектом) ${legacyName}|${legacyName} — экспериментальный проект|^# ${legacyName} rotating flagpole finial|${legacyName} is an experimental rotating flagpole-finial project`, 'm');
  for (const file of paths) assert.doesNotMatch(fs.readFileSync(path.join(root, file), 'utf8'), stale, file);
});
