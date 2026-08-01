/*
 * Защищает три исправленных контракта прошивки статически: BLE не открывается
 * после Deep-sleep, PIN не публикуется через GATT, VEML7700 имеет fail-safe.
 * Тест не компилирует ESP32-код и не заменяет аппаратный стенд. §ble0001 §blesec1 §fwfail1
 */
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const main = readFileSync(resolve(repoRoot, 'electronics/firmware/esp32_c3_crucian_v06/src/main.cpp'), 'utf8');
const config = readFileSync(resolve(repoRoot, 'electronics/firmware/esp32_c3_crucian_v06/include/config.h'), 'utf8');

describe('Crucian firmware safety contracts', () => {
  it('retains BLE lock across Deep-sleep and clears it on power-on', () => {
    assert.match(main, /RTC_DATA_ATTR bool bleLockedUntilPowerCycleRtc/);
    assert.match(main, /resetReason == ESP_RST_POWERON/);
    assert.match(main, /if \(!bleLockedUntilPowerCycleRtc\)\s*\{\s*setupBle\(\)/s);
    assert.match(main, /bleLockedUntilPowerCycleRtc = true;[\s\S]*btStop\(\)/);
  });

  it('does not expose the current PIN through the config characteristic', () => {
    assert.doesNotMatch(main, /["'](?:;)?PIN=/);
    assert.match(main, /PIN_DEFAULT=/);
    assert.match(config, /FACTORY_SETUP_PIN = 123456/);
  });

  it('turns the load off after persistent VEML7700 errors', () => {
    assert.match(config, /SENSOR_ERROR_LIMIT = 3/);
    assert.match(main, /RTC_DATA_ATTR uint8_t sensorErrorCountRtc/);
    assert.match(main, /state\.sensorFault = state\.sensorErrorCount >= cfg::SENSOR_ERROR_LIMIT/);
    assert.match(main, /if \(state\.sensorFault\)[\s\S]*fadeTo\(0\)/);
    assert.match(main, /SENSOR=/);
  });
});
