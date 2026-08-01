#include <Arduino.h>
#include <Wire.h>
#include <Preferences.h>
#include <NimBLEDevice.h>
#include <Adafruit_VEML7700.h>
#include <esp_sleep.h>
#include <esp_system.h>
#include <cmath>
#include "config.h"

static const NimBLEUUID SERVICE_UUID("d7a10000-4d22-4d86-9287-b5f168000001");
static const NimBLEUUID STATUS_UUID("d7a10000-4d22-4d86-9287-b5f168000002");
static const NimBLEUUID CONTROL_UUID("d7a10000-4d22-4d86-9287-b5f168000003");
static const NimBLEUUID CONFIG_UUID("d7a10000-4d22-4d86-9287-b5f168000004");

enum class WorkMode : uint8_t { Auto = 0, On = 1, Off = 2 };

Preferences prefs;
Adafruit_VEML7700 lightSensor;
NimBLEServer* bleServer = nullptr;
NimBLECharacteristic* statusChr = nullptr;
NimBLECharacteristic* controlChr = nullptr;
NimBLECharacteristic* configChr = nullptr;

RTC_DATA_ATTR bool lampEnabledRtc = false;
RTC_DATA_ATTR uint8_t manualBrightnessRtc = cfg::DEFAULT_MANUAL_BRIGHTNESS;
RTC_DATA_ATTR WorkMode modeRtc = WorkMode::Auto;
RTC_DATA_ATTR uint32_t rtcStateMagic = 0;
RTC_DATA_ATTR bool bleLockedUntilPowerCycleRtc = false;
RTC_DATA_ATTR uint8_t sensorErrorCountRtc = 0;

static constexpr uint32_t RTC_STATE_MAGIC = 0x4352434Eu; // "CRCN"

struct State {
    bool bleWindowActive = true;
    bool bleAuthorized = false;
    bool keepBleUntilPowerLoss = false;
    bool bleForceOff = false;
    bool isConnected = false;
    bool serviceReady = false;
    bool lightSensorReady = false;
    bool sensorFault = false;
    uint8_t sensorErrorCount = 0;
    uint32_t powerOnMs = 0;
    uint32_t storedPin = cfg::FACTORY_SETUP_PIN;
    float dayLux = cfg::DEFAULT_DAY_LUX;
    float nightLux = cfg::DEFAULT_NIGHT_LUX;
    float lastLux = 0.0f;
    float lastTemp = 0.0f;
    float lastBattery = 0.0f;
    uint8_t currentBrightness = 0;
} state;

bool initializeLightSensor() {
    if (!lightSensor.begin()) {
        return false;
    }
    lightSensor.setGain(VEML7700_GAIN_1_8);
    lightSensor.setIntegrationTime(VEML7700_IT_100MS);
    return true;
}

bool readLux(float& value) {
    if (!state.lightSensorReady) {
        state.lightSensorReady = initializeLightSensor();
        if (!state.lightSensorReady) {
            return false;
        }
    }
    const float measured = lightSensor.readLux();
    if (!std::isfinite(measured) || measured < 0.0f) {
        state.lightSensorReady = false;
        return false;
    }
    value = measured;
    return true;
}

float readNtcTempC() {
    int raw = analogRead(cfg::PIN_NTC);
    if (raw <= 0) return -127.0f;
    constexpr float maxAdc = 4095.0f;
    float v = raw / maxAdc;
    if (v <= 0.0f || v >= 1.0f) return -127.0f;
    float r = cfg::NTC_FIXED_R * v / (1.0f - v);
    float invT = 1.0f / cfg::NTC_T0_K + log(r / cfg::NTC_R0) / cfg::NTC_BETA;
    return (1.0f / invT) - 273.15f;
}

float readBatteryVolts() {
    // Заглушка: при необходимости подключить делитель напряжения и скорректировать коэффициент.
    return 12.0f;
}

uint16_t percentToDuty(uint8_t percent) {
    percent = min<uint8_t>(percent, 100);
    return static_cast<uint16_t>((cfg::PWM_MAX * percent) / 100u);
}

void applyBrightness(uint8_t percent) {
    state.currentBrightness = min<uint8_t>(percent, 100);
    uint16_t duty = percentToDuty(state.currentBrightness);
    if (!cfg::PWM_ACTIVE_HIGH) {
        duty = cfg::PWM_MAX - duty;
    }
    ledcWrite(cfg::PWM_CHANNEL, duty);
    lampEnabledRtc = state.currentBrightness > 0;
}

void fadeTo(uint8_t targetPercent, uint16_t stepDelayMs = 18) {
    targetPercent = min<uint8_t>(targetPercent, 100);
    int current = state.currentBrightness;
    while (current != targetPercent) {
        current += (current < targetPercent) ? 1 : -1;
        applyBrightness(static_cast<uint8_t>(current));
        delay(stepDelayMs);
    }
}

String modeToString(WorkMode mode) {
    switch (mode) {
        case WorkMode::On: return "ON";
        case WorkMode::Off: return "OFF";
        default: return "AUTO";
    }
}

uint8_t computeAutoBrightness(float lux) {
    if (lux >= state.dayLux) return 0;
    if (lux <= state.nightLux) return 100;
    float span = state.dayLux - state.nightLux;
    if (span < 1.0f) return 100;
    float x = (state.dayLux - lux) / span;
    x = constrain(x, 0.0f, 1.0f);
    return static_cast<uint8_t>(20.0f + x * 80.0f); // от 20 до 100%
}

String buildStatusPayload() {
    String payload;
    payload.reserve(96);
    payload += "MODE=" + modeToString(modeRtc);
    payload += ";LUX=" + String(state.lastLux, 1);
    payload += ";TEMP=" + String(state.lastTemp, 1);
    payload += ";BAT=" + String(state.lastBattery, 1);
    payload += ";BRI=" + String(state.currentBrightness);
    payload += ";BLE=" + String(state.bleForceOff ? 0 : 1);
    const char* sensorStatus = state.sensorFault ? "FAULT" : (state.sensorErrorCount > 0 ? "RETRY" : "OK");
    payload += ";SENSOR=" + String(sensorStatus);
    return payload;
}

String buildConfigPayload() {
    String payload;
    payload.reserve(128);
    payload += "NAME=" + String(cfg::DEVICE_NAME);
    payload += ";DAY=" + String(state.dayLux, 1);
    payload += ";NIGHT=" + String(state.nightLux, 1);
    // Сам PIN никогда не возвращаем через GATT, даже по зашифрованному каналу.
    payload += ";PIN_DEFAULT=" + String(state.storedPin == cfg::FACTORY_SETUP_PIN ? 1 : 0);
    payload += ";WINDOW_MIN=60";
    return payload;
}

void notifyStatus() {
    if (statusChr == nullptr) return;
    const String payload = buildStatusPayload();
    statusChr->setValue(payload.c_str());
    statusChr->notify();
}

void saveConfig() {
    prefs.putULong("pin", state.storedPin);
    prefs.putFloat("dayLux", state.dayLux);
    prefs.putFloat("nightLux", state.nightLux);
}

void loadConfig() {
    prefs.begin("crucian", false);
    state.storedPin = prefs.getULong("pin", cfg::FACTORY_SETUP_PIN);
    state.dayLux = prefs.getFloat("dayLux", cfg::DEFAULT_DAY_LUX);
    state.nightLux = prefs.getFloat("nightLux", cfg::DEFAULT_NIGHT_LUX);
    NimBLEDevice::setSecurityPasskey(state.storedPin);
}

void stopBle() {
    // RTC-память переживает Deep-sleep: таймерное пробуждение не должно заново
    // открывать сервисное окно. Полный power cycle очистит блокировку в setup().
    bleLockedUntilPowerCycleRtc = true;
    state.bleForceOff = true;
    NimBLEDevice::stopAdvertising();
    btStop();
}

void startAdvertising() {
    NimBLEAdvertising* adv = NimBLEDevice::getAdvertising();
    adv->setName(cfg::DEVICE_NAME);
    adv->addServiceUUID(SERVICE_UUID);
    adv->enableScanResponse(true);
    adv->start();
}

class ControlCallbacks : public NimBLECharacteristicCallbacks {
    void onWrite(NimBLECharacteristic* pCharacteristic, NimBLEConnInfo& connInfo) override {
        std::string raw = pCharacteristic->getValue();
        String command(raw.c_str());
        command.trim();
        command.toUpperCase();

        if (command == "STATUS?") {
            notifyStatus();
            return;
        }
        if (command.startsWith("MODE:")) {
            String arg = command.substring(5);
            if (arg == "AUTO") {
                modeRtc = WorkMode::Auto;
            } else if (arg == "ON") {
                modeRtc = WorkMode::On;
            } else if (arg == "OFF") {
                modeRtc = WorkMode::Off;
            }
        } else if (command.startsWith("BRIGHTNESS:")) {
            int value = command.substring(11).toInt();
            manualBrightnessRtc = static_cast<uint8_t>(constrain(value, 0, 100));
            if (modeRtc == WorkMode::On) {
                fadeTo(manualBrightnessRtc);
            }
        } else if (command == "BLE:OFF") {
            state.keepBleUntilPowerLoss = false;
            notifyStatus();
            delay(200);
            stopBle();
            return;
        } else if (command == "CALIBRATE:DAY") {
            if (!state.sensorFault && state.sensorErrorCount == 0 && state.lastLux > state.nightLux) {
                state.dayLux = state.lastLux;
                saveConfig();
            }
        } else if (command == "CALIBRATE:NIGHT") {
            if (!state.sensorFault && state.sensorErrorCount == 0 && state.lastLux < state.dayLux) {
                state.nightLux = state.lastLux;
                saveConfig();
            }
        } else if (command.startsWith("PIN:")) {
            // PIN:old,new
            String pair = command.substring(4);
            int comma = pair.indexOf(',');
            if (comma > 0) {
                uint32_t oldPin = pair.substring(0, comma).toInt();
                uint32_t newPin = pair.substring(comma + 1).toInt();
                if (oldPin == state.storedPin && newPin >= 100000 && newPin <= 999999) {
                    state.storedPin = newPin;
                    saveConfig();
                    NimBLEDevice::deleteAllBonds();
                    NimBLEDevice::setSecurityPasskey(state.storedPin);
                    bleServer->disconnect(connInfo);
                }
            }
        }
        notifyStatus();
    }
};

class ConfigCallbacks : public NimBLECharacteristicCallbacks {
    void onRead(NimBLECharacteristic* pCharacteristic, NimBLEConnInfo& connInfo) override {
        const String payload = buildConfigPayload();
        pCharacteristic->setValue(payload.c_str());
    }
};

class ServerCallbacks : public NimBLEServerCallbacks {
    void onConnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo) override {
        state.isConnected = true;
    }
    void onDisconnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo, int reason) override {
        state.isConnected = false;
        if (!state.bleForceOff && (state.bleWindowActive || state.keepBleUntilPowerLoss)) {
            NimBLEDevice::startAdvertising();
        }
    }
    uint32_t onPassKeyDisplay() override {
        return state.storedPin;
    }
    void onConfirmPassKey(NimBLEConnInfo& connInfo, uint32_t pin) override {
        NimBLEDevice::injectConfirmPasskey(connInfo, true);
    }
    void onAuthenticationComplete(NimBLEConnInfo& connInfo) override {
        if (!connInfo.isEncrypted() || !connInfo.isBonded()) {
            NimBLEDevice::getServer()->disconnect(connInfo);
            return;
        }
        state.bleAuthorized = true;
        state.keepBleUntilPowerLoss = true;
    }
} serverCallbacks;

void setupBle() {
    NimBLEDevice::init(cfg::DEVICE_NAME);
    NimBLEDevice::setSecurityIOCap(BLE_HS_IO_DISPLAY_ONLY);
    NimBLEDevice::setSecurityAuth(true, true, true);
    NimBLEDevice::setSecurityPasskey(state.storedPin);
    bleServer = NimBLEDevice::createServer();
    bleServer->setCallbacks(&serverCallbacks);
    NimBLEService* service = bleServer->createService(SERVICE_UUID);
    statusChr = service->createCharacteristic(STATUS_UUID,
        NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY | NIMBLE_PROPERTY::READ_ENC);
    controlChr = service->createCharacteristic(CONTROL_UUID,
        NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_ENC);
    configChr = service->createCharacteristic(CONFIG_UUID,
        NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::READ_ENC);
    controlChr->setCallbacks(new ControlCallbacks());
    configChr->setCallbacks(new ConfigCallbacks());
    bleServer->start();
    startAdvertising();
    state.serviceReady = true;
}

void setup() {
    Serial.begin(115200);
    delay(200);

    const esp_reset_reason_t resetReason = esp_reset_reason();
    if (rtcStateMagic != RTC_STATE_MAGIC || resetReason == ESP_RST_POWERON) {
        rtcStateMagic = RTC_STATE_MAGIC;
        bleLockedUntilPowerCycleRtc = false;
        sensorErrorCountRtc = 0;
    }
    state.bleForceOff = bleLockedUntilPowerCycleRtc;
    state.bleWindowActive = !bleLockedUntilPowerCycleRtc;
    state.sensorErrorCount = sensorErrorCountRtc;
    state.sensorFault = state.sensorErrorCount >= cfg::SENSOR_ERROR_LIMIT;
    state.powerOnMs = millis();
    pinMode(cfg::PIN_PWM, OUTPUT);
    ledcSetup(cfg::PWM_CHANNEL, cfg::PWM_FREQ_HZ, cfg::PWM_RES_BITS);
    ledcAttachPin(cfg::PIN_PWM, cfg::PWM_CHANNEL);
    applyBrightness(0);

    Wire.begin(cfg::PIN_I2C_SDA, cfg::PIN_I2C_SCL);
    state.lightSensorReady = initializeLightSensor();

    loadConfig();
    if (!bleLockedUntilPowerCycleRtc) {
        setupBle();
    } else {
        Serial.println("BLE remains locked until the next power cycle");
    }
}

void loop() {
    float measuredLux = 0.0f;
    const bool sensorMeasurementValid = readLux(measuredLux);
    if (sensorMeasurementValid) {
        state.lastLux = measuredLux;
        state.sensorErrorCount = 0;
        sensorErrorCountRtc = 0;
        state.sensorFault = false;
    } else {
        if (state.sensorErrorCount < cfg::SENSOR_ERROR_LIMIT) {
            ++state.sensorErrorCount;
        }
        sensorErrorCountRtc = state.sensorErrorCount;
        state.sensorFault = state.sensorErrorCount >= cfg::SENSOR_ERROR_LIMIT;
        Serial.printf("VEML7700 read error %u/%u\n", state.sensorErrorCount, cfg::SENSOR_ERROR_LIMIT);
    }
    state.lastTemp = readNtcTempC();
    state.lastBattery = readBatteryVolts();

    if (state.sensorFault) {
        // После трёх ошибок выключаем силовую нагрузку независимо от режима.
        if (state.currentBrightness != 0) fadeTo(0);
    } else if (!sensorMeasurementValid) {
        // До достижения порога ошибки не меняем нагрузку по устаревшим данным.
    } else if (modeRtc == WorkMode::Off) {
        if (state.currentBrightness != 0) fadeTo(0);
    } else if (modeRtc == WorkMode::On) {
        if (state.currentBrightness != manualBrightnessRtc) fadeTo(manualBrightnessRtc);
    } else {
        uint8_t target = computeAutoBrightness(state.lastLux);
        if (target != state.currentBrightness) fadeTo(target, 10);
    }

    if (state.serviceReady && !state.bleForceOff) {
        notifyStatus();
    }

    const bool bleSessionAllowed = state.keepBleUntilPowerLoss || (millis() - state.powerOnMs) < cfg::BLE_IDLE_WINDOW_MS;
    state.bleWindowActive = bleSessionAllowed;
    if (!bleSessionAllowed && !state.isConnected && !state.keepBleUntilPowerLoss && !state.bleForceOff) {
        stopBle();
    }

    // Экономим энергию: при выключенной лампе и отключённом BLE уходим в глубокий сон.
    if (state.currentBrightness == 0 && state.bleForceOff) {
        Serial.println("Entering deep sleep for day mode");
        delay(100);
        esp_sleep_enable_timer_wakeup(static_cast<uint64_t>(cfg::DAY_SLEEP_SEC) * 1000000ULL);
        esp_deep_sleep_start();
    }

    delay(state.currentBrightness > 0 ? cfg::NIGHT_RECHECK_MS : cfg::DAY_RECHECK_MS);
}
