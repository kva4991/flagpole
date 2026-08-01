/*
 * Проверяет навигационный контракт документации локальным детерминированным
 * аудитом. Проектную истинность текста и внешний URL тест не подтверждает. §docqa01
 */
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { auditDocumentation } from '../tools/quality/documentationAudit.mjs';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const ignored = new Set(['.build', '.git', '.gradle', '.pio', 'build', 'node_modules']);

function markdownTree(root) {
  const paths = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    if (entry.isDirectory() && ignored.has(entry.name)) continue;
    const path = join(root, entry.name);
    if (entry.isDirectory()) paths.push(...markdownTree(path));
    else if (entry.name.endsWith('.md')) paths.push(relative(repoRoot, path).replaceAll('\\', '/'));
  }
  return paths;
}

describe('documentation contract', () => {
  it('keeps local links, registered tags and npm commands valid', () => {
    const report = auditDocumentation(markdownTree(repoRoot), { repoRoot });
    assert.deepEqual(report.brokenLinks, []);
    assert.deepEqual(report.unknownTags, []);
    assert.deepEqual(report.missingNpmScripts, []);
  });

  it('keeps the agent synchronization contract explicit', () => {
    const guidelines = readFileSync(resolve(repoRoot, 'AGENTS.md'), 'utf8');
    for (const requiredText of [
      'Когда обязательно обновлять карточки каталога',
      'Когда обязательно обновлять чертежи и 3D на странице',
      'catalog/components.json',
      'catalog/drawings.json',
      'npm.cmd run catalog:generate',
      'npm.cmd run catalog:check',
      'GitHub Pages-сайт пока не настроен',
    ]) {
      assert.match(guidelines, new RegExp(requiredText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
    }
  });
});
