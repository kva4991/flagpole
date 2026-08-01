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
    assert.match(html, /фото продавца/);
    assert.match(html, /справочное изображение/);
    assert.match(html, /Solaris2006, Wikimedia Commons, CC BY-SA 3\.0/);
    assert.match(html, /KBXlife case for 2\/4\/6 × 18650/);
    assert.match(html, /это не принято как подтверждённый рейтинг IPX7/);
    assert.match(html, /ESP32 C3 Mini Plus \/ SuperMini Plus V2\.0/);
    assert.match(html, /Вид платы с обратной стороны/);
    assert.match(html, /Senring M125-0205 slip ring — 12\.5 mm, 2CH, 5A/);
    assert.match(html, /eletechsup synchronous DC-DC buck converter — 5V, 4A\/5A/);
    assert.match(html, /TZT optoisolated LR7843 MOSFET PWM module — 30V/);
    assert.match(html, /VEML7700 ambient light sensor module — Gravity I2C/);
    assert.match(html, /XUNATA Round Neon Light — 12V, 16 mm, 240 LED\/m/);
    assert.match(html, /Carbon-fiber fishing-rod repair piece — Ø5 × 100 mm/);
    assert.match(html, /Oxford 210D PU 2000 fabric — neon orange/);
    assert.match(html, /Silver reflective fabric/);
    assert.match(html, /10 ft stainless-steel ground flagpole with five-prong base/);
    assert.match(html, /ELEGOO TPU 95A filament — white, 1\.75 mm, 1 kg/);
    assert.match(html, /ERYONE NEW TPU 85A filament/);
    assert.match(html, /2-pin waterproof connectors with 20 AWG wires — 5 pairs/);
    assert.match(html, /PUMUDDSY RXEF075 resettable PPTC fuse — 0\.75A, 20 pcs/);
  });
});
