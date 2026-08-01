/*
 * Защищает исправленные контракты прошивки статически: BLE не открывается
 * после Deep-sleep, PIN не публикуется через GATT, VEML7700 имеет fail-safe,
 * климатические датчики не подменяют световой fail-safe, а батарея не
 * отображается без физического измерительного тракта.
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
const platformio = readFileSync(resolve(repoRoot, 'electronics/firmware/esp32_c3_crucian_v06/platformio.ini'), 'utf8');

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
    assert.match(main, /deleteAllBonds/);
  });

  it('turns the load off after persistent VEML7700 errors', () => {
    assert.match(config, /SENSOR_ERROR_LIMIT = 3/);
    assert.match(main, /RTC_DATA_ATTR uint8_t sensorErrorCountRtc/);
    assert.match(main, /state\.sensorFault = state\.sensorErrorCount >= cfg::SENSOR_ERROR_LIMIT/);
    assert.match(main, /if \(state\.sensorFault\)[\s\S]*fadeTo\(0\)/);
    assert.match(main, /SENSOR=/);
  });

  it('does not expose or fake battery voltage', () => {
    assert.doesNotMatch(main, /readBatteryVolts/);
    assert.doesNotMatch(main, /;BAT=/);
  });

  it('disambiguates Arduino String decimal formatting', () => {
    assert.match(main, /String\(value, static_cast<unsigned int>\(digits\)\)/);
  });

  it('uses the ESP32-C3 USB serial and C++17 build contract', () => {
    assert.match(platformio, /-std=gnu\+\+17/);
    assert.match(platformio, /ARDUINO_USB_MODE=1/);
    assert.match(platformio, /ARDUINO_USB_CDC_ON_BOOT=1/);
    assert.match(main, /createService\(SERVICE_UUID\)/);
    assert.match(main, /service->start\(\)/);
  });

  it('uses the combined AHT20 plus BMP280 module without NTC', () => {
    assert.doesNotMatch(main, /readNtcTempC|analogRead\(cfg::PIN_NTC\)/);
    assert.doesNotMatch(config, /PIN_NTC|NTC_BETA|NTC_FIXED_R/);
    assert.match(config, /AHT20_I2C_ADDRESS = 0x38/);
    assert.match(main, /chipId != 0x58/);
    assert.match(main, /Adafruit_AHTX0/);
    assert.match(main, /ENV=/);
    assert.match(main, /PARTIAL/);
    assert.match(main, /;HUM=/);
    assert.match(main, /;PRESS=/);
    assert.match(main, /;ENV=/);
    assert.match(main, /;BARO=/);
  });
});
