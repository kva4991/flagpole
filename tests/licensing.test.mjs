import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import test from 'node:test';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');

test('repository has explicit split hardware/software licensing', () => {
  const map = readFileSync(resolve(root, 'LICENSE.md'), 'utf8');
  assert.match(map, /CERN-OHL-S-2\.0/);
  assert.match(map, /MIT License/);
  assert.match(map, /Source Location: https:\/\/github\.com\/kva4991\/flagpole/);
  assert.match(map, /not relicensed/i);
  assert.equal(existsSync(resolve(root, 'LICENSE_NOT_SELECTED_RU.md')), false);
});

test('bundled licence texts are complete and unambiguous', () => {
  const cern = readFileSync(resolve(root, 'LICENSES/CERN-OHL-S-2.0.txt'), 'utf8');
  const mit = readFileSync(resolve(root, 'LICENSES/MIT.txt'), 'utf8');

  assert.match(cern, /^CERN Open Hardware Licence Version 2 - Strongly Reciprocal/);
  assert.match(cern, /1\.8 'Complete Source'/);
  assert.match(cern, /4 Making and Conveying Products/);
  assert.match(cern, /8\.6 This Licence shall not be enforceable/);
  assert.match(mit, /^MIT License/);
  assert.match(mit, /Permission is hereby granted, free of charge/);
  assert.match(mit, /THE SOFTWARE IS PROVIDED "AS IS"/);
});

test('project rules preserve third-party licensing', () => {
  const agents = readFileSync(resolve(root, 'AGENTS.md'), 'utf8');
  const sources = readFileSync(resolve(root, 'catalog/images/SOURCES.md'), 'utf8');
  assert.match(agents, /Сторонние изображения/);
  assert.match(agents, /Не удалять и не заменять существующий SPDX/);
  assert.match(sources, /лицензия/);
});
