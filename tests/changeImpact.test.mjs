/*
 * Проверяет, что карта влияния не считает критическую механику или прошивку
 * обычной текстовой правкой. Реальные сборки и испытания тест не запускает. §impact
 */
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { inspectPaths } from '../tools/quality/changeImpact.mjs';

describe('change impact map', () => {
  it('marks firmware and mechanics as critical', () => {
    assert.equal(inspectPaths(['electronics/firmware/esp32_c3_crucian_v06/src/main.cpp']).risk, 'critical');
    assert.equal(inspectPaths(['mechanical/generate_models_v05.py']).risk, 'critical');
  });

  it('keeps documentation-only work low risk', () => {
    const report = inspectPaths(['docs/current-implementation-status.ru.md']);
    assert.equal(report.risk, 'low');
    assert.deepEqual(report.unknown, []);
  });

  it('reports unknown paths instead of hiding them', () => {
    const report = inspectPaths(['experimental/unknown.bin']);
    assert.equal(report.risk, 'high');
    assert.deepEqual(report.unknown, ['experimental/unknown.bin']);
  });
});
