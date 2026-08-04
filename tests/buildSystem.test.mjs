import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import { classify } from '../scripts/classifyCiChanges.mjs';
import { readLfsPointer } from '../scripts/lfsPointer.mjs';

const root = path.resolve(import.meta.dirname, '..');
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), 'utf8');

test('CI change classifier avoids unrelated LFS, Android and firmware jobs', () => {
  assert.deepEqual(classify(['docs/README.ru.md']), {
    mechanical: false,
    android: false,
    firmware: false,
  });
  assert.deepEqual(classify(['mechanical/generate_models_v06.py']), {
    mechanical: true,
    android: false,
    firmware: false,
  });
  assert.deepEqual(classify(['android/crucian-control/app/build.gradle.kts']), {
    mechanical: false,
    android: true,
    firmware: false,
  });
  assert.deepEqual(classify(['__all__']), {
    mechanical: true,
    android: true,
    firmware: true,
  });
});

test('LFS pointer reader exposes the original content hash and byte size', () => {
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'flagpole-lfs-'));
  const file = path.join(folder, 'model.glb');
  const oid = 'a'.repeat(64);
  fs.writeFileSync(file, `version https://git-lfs.github.com/spec/v1\noid sha256:${oid}\nsize 427123456\n`);
  assert.deepEqual(readLfsPointer(file), { oid, size: 427123456 });
  fs.rmSync(folder, { recursive: true, force: true });
});

test('checksum and catalog generators understand LFS pointers without downloading assets', () => {
  assert.match(read('scripts/checkChecksums.mjs'), /readLfsPointer/);
  assert.match(read('scripts/checkChecksums.mjs'), /lfsPointer\.oid/);
  assert.match(read('scripts/generateComponentCatalog.mjs'), /readLfsPointer/);
  assert.match(read('scripts/generateComponentCatalog.mjs'), /\?\.size/);
});

test('LFS policy tracks STL and GLB but keeps PNG in ordinary Git', () => {
  const attributes = read('.gitattributes');
  assert.match(attributes, /^\*\.stl filter=lfs diff=lfs merge=lfs -text$/m);
  assert.match(attributes, /^\*\.glb filter=lfs diff=lfs merge=lfs -text$/m);
  assert.match(attributes, /^\*\.step filter=lfs diff=lfs merge=lfs -text$/m);
  assert.match(attributes, /^\*\.png binary$/m);
  assert.doesNotMatch(attributes, /^\*\.png filter=lfs/m);
});

test('unified build orders generation before catalog and final validation', () => {
  const build = read('scripts/build.mjs');
  assert.ok(build.indexOf("cadPython('mechanical/generate_build123d_canonical_v076.py')") < build.indexOf("npmRun('catalog:generate')"));
  assert.match(build, /function generateLegacyReferencesOnExplicitRequest/);
  assert.match(build, /mode === 'legacy-references'/);
  assert.ok(build.indexOf("npmRun('checksums:update')") < build.indexOf('validateProject();'));
  assert.match(read('build.cmd'), /tools\\windows\\build\.ps1/);
  assert.match(read('tools/windows/build.ps1'), /FLAGPOLE_PYTHON/);
  assert.match(read('tools/windows/build.ps1'), /FLAGPOLE_CAD_PYTHON/);
});

test('CI has one conditional LFS download and unified mechanical build', () => {
  const workflow = read('.github/workflows/validate.yml');
  assert.equal((workflow.match(/git lfs pull/g) ?? []).length, 1);
  assert.match(workflow, /if: needs\.quality\.outputs\.mechanical == 'true'/);
  assert.match(workflow, /run: npm run build:ci/);
  assert.equal((workflow.match(/lfs: false/g) ?? []).length, 4);
  assert.match(workflow, /cancel-in-progress: true/);
});
