/*
 * Защищает формат и индекс ADR. Тест не доказывает техническую правильность
 * решения и не заменяет измерения или стендовые испытания. §adrproc
 */
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const decisionRoot = resolve(repoRoot, 'docs/architecture/decisions');
const decisionFiles = readdirSync(decisionRoot).filter((name) => /^\d{4}-.+\.ru\.md$/.test(name)).sort();

describe('architecture decision records', () => {
  it('keeps sequential records with required reasoning sections', () => {
    assert.ok(decisionFiles.length >= 4);
    decisionFiles.forEach((file, index) => {
      const source = readFileSync(resolve(decisionRoot, file), 'utf8');
      const number = String(index + 1).padStart(4, '0');
      assert.equal(file.slice(0, 4), number);
      assert.match(source, new RegExp(`^# ADR-${number}: `));
      assert.match(source, /^- Статус: (?:Предложено|Принято|Отклонено|Заменено ADR-\d{4})$/m);
      assert.match(source, /^- Дата: \d{4}-\d{2}-\d{2}$/m);
      for (const heading of ['Контекст', 'Рассмотренные варианты', 'Решение', 'Последствия', 'Проверка', 'Когда пересматривать']) {
        assert.match(source, new RegExp(`^## ${heading}$`, 'm'));
      }
    });
  });

  it('indexes every ADR and keeps decision-local links alive', () => {
    const index = readFileSync(resolve(decisionRoot, 'README.ru.md'), 'utf8');
    for (const file of decisionFiles) {
      assert.match(index, new RegExp(`\\(${file.replaceAll('.', '\\.')}\\)`));
      const source = readFileSync(resolve(decisionRoot, file), 'utf8');
      for (const match of source.matchAll(/\[[^\]]+\]\(([^)]+)\)/g)) {
        if (/^(?:https?:|#)/.test(match[1])) continue;
        assert.ok(existsSync(resolve(decisionRoot, match[1])), `${file}: ${match[1]}`);
      }
    }
  });
});
