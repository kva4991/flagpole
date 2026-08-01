/*
 * Проверяет, что опубликованный HTML-каталог воспроизводится из JSON-источника.
 * Доступность внешних ссылок и фактические параметры деталей не проверяются. §catalog
 */
import { spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');

describe('component catalog', () => {
  it('matches catalog/components.json', () => {
    const result = spawnSync(process.execPath, ['scripts/generateComponentCatalog.mjs', '--check'], {
      cwd: repoRoot,
      encoding: 'utf8',
    });
    assert.equal(result.status, 0, result.stderr || result.stdout);
  });

  it('contains the requested columns and data-completion controls', () => {
    const html = fs.readFileSync(resolve(repoRoot, 'catalog/catalog.html'), 'utf8');
    for (const heading of ['ID', 'Картинка', 'Возможные названия компонента', 'Зачем он нужен', 'Описание или покупка']) {
      assert.match(html, new RegExp(`<th>${heading}</th>`));
    }
    assert.match(html, /Только позиции, которые нужно уточнить/);
    assert.match(html, /data-id="cmp-001"/);
  });
});
