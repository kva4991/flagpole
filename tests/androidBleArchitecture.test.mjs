import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const root = process.cwd();
const client = fs.readFileSync(path.join(root, 'android/crucian-control/app/src/main/java/ru/superpommelsandflag/crucian/CrucianBleClient.kt'), 'utf8');
const models = fs.readFileSync(path.join(root, 'android/crucian-control/app/src/main/java/ru/superpommelsandflag/crucian/BleModels.kt'), 'utf8');

test('Android BLE client has queue, timeouts and lifecycle cleanup', () => {
  assert.match(client, /ArrayDeque<GattOperation>/);
  assert.match(client, /activeOperation/);
  assert.match(client, /OPERATION_TIMEOUT_MS/);
  assert.match(client, /localGatt\.close\(\)/);
  assert.match(client, /unregisterReceiver/);
});

test('Android uses modern API 33 writes with legacy fallback', () => {
  assert.match(client, /Build\.VERSION\.SDK_INT >= 33/);
  assert.match(client, /writeDescriptor\(descriptor, value\)/);
  assert.match(client, /writeCharacteristic\(/);
  assert.match(client, /@Suppress\("DEPRECATION"\)/);
});

test('Android defines explicit BLE phases', () => {
  for (const phase of ['SCANNING', 'CONNECTING', 'NEGOTIATING_MTU', 'BONDING', 'DISCOVERING_SERVICES', 'SUBSCRIBING', 'READING_CONFIGURATION', 'READY']) {
    assert.ok(models.includes(phase), `missing phase ${phase}`);
  }
});
