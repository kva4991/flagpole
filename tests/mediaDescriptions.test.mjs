import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { loadAndValidateMediaDescriptions, parseMediaDescription } from '../scripts/mediaDescriptions.mjs';

const root = process.cwd();
const media = JSON.parse(fs.readFileSync(path.join(root, 'catalog', 'drawings.json'), 'utf8'));
const records = [
  ...media.drawings.map(item => ({ ...item, catalogSection: 'drawings' })),
  ...media.models.map(item => ({ ...item, catalogSection: 'models' })),
  ...media.experimentalModels.map(item => ({ ...item, catalogSection: 'experimentalModels' })),
  ...media.printSessions.map(item => ({ ...item, catalogSection: 'printSessions' })),
];

test('each drawing, model and print session has exactly one detailed description with the same ID', () => {
  const { descriptions, failures } = loadAndValidateMediaDescriptions(root, media, { throwOnFailure: false });
  assert.deepEqual(failures, []);
  assert.equal(descriptions.size, records.length);
  assert.equal(records.length, 29);
  for (const item of records) {
    assert.equal(item.descriptionFile, `catalog/media-descriptions/${item.id}.md`);
    assert.equal(Object.hasOwn(item, 'description'), false, `duplicate JSON description for #${item.id}`);
    const description = descriptions.get(item.id);
    assert.ok(description, `missing description for #${item.id}`);
    assert.equal(description.metadata.id, item.id);
    assert.equal(description.metadata.catalogSection, item.catalogSection);
    assert.equal(description.metadata.mediaType, item.kind);
    assert.equal(description.metadata.mediaFile, item.file);
    assert.equal(description.metadata.title, item.title);
    assert.ok(description.body.replace(/\s/g, '').length >= 2500);
    for (const heading of [
      '## 0. Критический контракт',
      '### Критические элементы — нельзя потерять',
      '### Запрещено',
      '### Проверить после генерации',
    ]) {
      assert.match(description.body, new RegExp(heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
    }
  }
});

test('every media description starts with an actionable compact contract', () => {
  const { descriptions } = loadAndValidateMediaDescriptions(root, media);
  for (const [id, description] of descriptions) {
    const contractStart = description.body.indexOf('## 0. Критический контракт');
    const rationaleStart = description.body.indexOf('## 1. Назначение и границы');
    assert.ok(contractStart > 0 && contractStart < rationaleStart, `#${id}: compact contract must precede rationale`);
    const contract = description.body.slice(contractStart, rationaleStart);
    assert.ok((contract.match(/^- .+/gm) ?? []).length >= 7, `#${id}: compact contract is not actionable`);
  }
});

test('description directory has no orphan numeric markdown files', () => {
  const ids = new Set(records.map(item => item.id));
  const files = fs.readdirSync(path.join(root, 'catalog', 'media-descriptions'))
    .filter(name => /^\d{3}\.md$/.test(name));
  assert.equal(files.length, records.length);
  for (const file of files) assert.ok(ids.has(file.slice(0, -3)), `orphan description ${file}`);
});

test('catalog renders summaries from markdown and links every card to its same-ID description', () => {
  const html = fs.readFileSync(path.join(root, 'catalog', 'catalog.html'), 'utf8');
  for (const item of records) {
    const text = fs.readFileSync(path.join(root, item.descriptionFile), 'utf8');
    const { metadata } = parseMediaDescription(text, item.descriptionFile);
    assert.match(html, new RegExp(metadata.summary.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
    assert.match(html, new RegExp(`media-descriptions/${item.id}\\.md`));
    assert.match(html, new RegExp(`Подробное описание #${item.id}`));
  }
});

test('all user-visible catalog IDs receive exactly one hash prefix', () => {
  const html = fs.readFileSync(path.join(root, 'catalog', 'catalog.html'), 'utf8');
  for (const id of ['001', '009', '101', '125', '204', '210', '301', '303']) {
    assert.match(html, new RegExp(`#${id}`));
    assert.doesNotMatch(html, new RegExp(`##${id}`));
  }
  for (const id of ['petg-1', 'petg-10', 'tpu95-10', 'tpu85-3']) {
    assert.match(html, new RegExp(`#${id}`));
    assert.doesNotMatch(html, new RegExp(`##${id}`));
  }
});

test('generated description index contains every same-ID file and no stale rows', () => {
  const index = fs.readFileSync(path.join(root, 'catalog', 'media-descriptions', 'INDEX_RU.md'), 'utf8');
  for (const item of records) {
    assert.match(index, new RegExp(`\\[#${item.id}\\]\\(${item.id}\\.md\\)`));
    assert.match(index, new RegExp(item.file.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  }
  assert.equal((index.match(/^\| \[#\d{3}\]/gm) ?? []).length, records.length);
});
