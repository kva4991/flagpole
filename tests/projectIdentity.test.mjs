import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const root = process.cwd();
const identity = JSON.parse(fs.readFileSync(path.join(root, 'project_identity.json'), 'utf8'));
const firmware = fs.readFileSync(path.join(root, 'electronics/firmware/esp32_c3_crucian_v06/include/project_identity.h'), 'utf8');
const android = fs.readFileSync(path.join(root, 'android/crucian-control/app/src/main/java/ru/quicktickets/crucian/ProjectIdentity.kt'), 'utf8');
const strings = fs.readFileSync(path.join(root, 'android/crucian-control/app/src/main/res/values/strings.xml'), 'utf8');

test('project identity is generated into firmware and Android', () => {
  assert.ok(firmware.includes(identity.projectDisplayName));
  assert.ok(firmware.includes(identity.bluetoothDeviceName));
  assert.ok(android.includes(identity.projectDisplayName));
  assert.ok(android.includes(identity.bluetoothDeviceName));
  assert.ok(strings.includes(identity.projectDisplayName));
});
