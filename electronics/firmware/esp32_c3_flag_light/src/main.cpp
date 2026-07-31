#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_VEML7700.h>

#include <algorithm>
#include <array>
#include <cmath>

#include "driver/gpio.h"
#include "esp_sleep.h"

#include "config.h"

using namespace FlagLightConfig;

namespace {

Adafruit_VEML7700 lightSensor;

// Values stored in RTC memory survive Deep-sleep, but are reset on power loss.
RTC_DATA_ATTR bool rtcLampOn = false;
RTC_DATA_ATTR uint8_t rtcDarkCount = 0;
RTC_DATA_ATTR uint8_t rtcLightCount = 0;
RTC_DATA_ATTR uint8_t rtcSensorFailureCount = 0;
RTC_DATA_ATTR uint32_t rtcCycleNumber = 0;

constexpr gpio_num_t LAMP_GPIO = static_cast<gpio_num_t>(PIN_LAMP_CONTROL);

int lampLevel(const bool on) {
    const bool high = LAMP_ACTIVE_HIGH ? on : !on;
    return high ? HIGH : LOW;
}

void logLine(const char *message) {
    if constexpr (ENABLE_SERIAL_LOG) {
        Serial.println(message);
    }
}

void restoreLampOutputAfterWake() {
    // The output may still be held from the previous Deep-sleep cycle.
    // Configure the internal output state first, then release the pad hold;
    // this avoids a short pulse on the lamp control line.
    pinMode(PIN_LAMP_CONTROL, OUTPUT);
    digitalWrite(PIN_LAMP_CONTROL, lampLevel(rtcLampOn));
    gpio_hold_dis(LAMP_GPIO);
    digitalWrite(PIN_LAMP_CONTROL, lampLevel(rtcLampOn));
}

void setLamp(const bool on) {
    rtcLampOn = on;
    gpio_hold_dis(LAMP_GPIO);
    pinMode(PIN_LAMP_CONTROL, OUTPUT);
    digitalWrite(PIN_LAMP_CONTROL, lampLevel(on));
}

void holdLampOutputForDeepSleep() {
    pinMode(PIN_LAMP_CONTROL, OUTPUT);
    digitalWrite(PIN_LAMP_CONTROL, lampLevel(rtcLampOn));
    gpio_hold_en(LAMP_GPIO);
    gpio_deep_sleep_hold_en();
}

bool readMedianLux(float &luxOut) {
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    Wire.setClock(100000);

    if (!lightSensor.begin(&Wire)) {
        return false;
    }

    lightSensor.enable(true);

    std::array<float, LUX_SAMPLE_COUNT> values{};
    uint8_t validCount = 0;

    for (uint8_t i = 0; i < LUX_SAMPLE_COUNT; ++i) {
        const float lux = lightSensor.readLux(VEML_LUX_AUTO);
        if (std::isfinite(lux) && lux >= 0.0F) {
            values[validCount++] = lux;
        }
        delay(SAMPLE_PAUSE_MS);
    }

    // Put the VEML7700 into shutdown before the ESP enters Deep-sleep.
    lightSensor.enable(false);

    if (validCount < 3) {
        return false;
    }

    std::sort(values.begin(), values.begin() + validCount);
    luxOut = values[validCount / 2];
    return true;
}

void applyLuxDecision(const float lux) {
    if (!rtcLampOn) {
        rtcLightCount = 0;

        if (lux <= LUX_TURN_ON) {
            if (rtcDarkCount < UINT8_MAX) {
                ++rtcDarkCount;
            }
        } else {
            rtcDarkCount = 0;
        }

        if (rtcDarkCount >= DARK_CONFIRMATIONS) {
            setLamp(true);
            rtcDarkCount = 0;
        }
        return;
    }

    rtcDarkCount = 0;

    if (lux >= LUX_TURN_OFF) {
        if (rtcLightCount < UINT8_MAX) {
            ++rtcLightCount;
        }
    } else {
        rtcLightCount = 0;
    }

    if (rtcLightCount >= LIGHT_CONFIRMATIONS) {
        setLamp(false);
        rtcLightCount = 0;
    }
}

void handleSensorFailure() {
    if (rtcSensorFailureCount < UINT8_MAX) {
        ++rtcSensorFailureCount;
    }

    // Preserve the previous state through brief I2C errors. After repeated
    // failures, turn the lamp off so a broken or flooded sensor cannot leave
    // the light permanently on during daytime.
    if (rtcSensorFailureCount >= SENSOR_FAILURE_LIMIT) {
        rtcDarkCount = 0;
        rtcLightCount = 0;
        setLamp(false);
    }
}

void runMeasurementCycle() {
    ++rtcCycleNumber;

    float lux = 0.0F;
    const bool sensorOk = readMedianLux(lux);

    if (sensorOk) {
        rtcSensorFailureCount = 0;
        applyLuxDecision(lux);

        if constexpr (ENABLE_SERIAL_LOG) {
            Serial.printf(
                "cycle=%lu lux=%.3f lamp=%s dark=%u light=%u failures=%u\n",
                static_cast<unsigned long>(rtcCycleNumber),
                lux,
                rtcLampOn ? "ON" : "OFF",
                rtcDarkCount,
                rtcLightCount,
                rtcSensorFailureCount
            );
        }
    } else {
        handleSensorFailure();
        if constexpr (ENABLE_SERIAL_LOG) {
            Serial.printf(
                "cycle=%lu sensor=ERROR lamp=%s failures=%u\n",
                static_cast<unsigned long>(rtcCycleNumber),
                rtcLampOn ? "ON" : "OFF",
                rtcSensorFailureCount
            );
        }
    }
}

[[noreturn]] void enterDeepSleep() {
    holdLampOutputForDeepSleep();
    esp_sleep_enable_timer_wakeup(
        static_cast<uint64_t>(SLEEP_SECONDS) * 1000000ULL
    );

    if constexpr (ENABLE_SERIAL_LOG) {
        Serial.flush();
    }

    esp_deep_sleep_start();
    while (true) {
        delay(1000);
    }
}

} // namespace

void setup() {
    if constexpr (ENABLE_SERIAL_LOG) {
        Serial.begin(115200);
        delay(200);
    }

    // A cold power-up starts safely with the lamp off. Deep-sleep wakeups keep
    // the values stored in RTC memory.
    const esp_sleep_wakeup_cause_t wakeCause = esp_sleep_get_wakeup_cause();
    if (wakeCause == ESP_SLEEP_WAKEUP_UNDEFINED) {
        rtcLampOn = false;
        rtcDarkCount = 0;
        rtcLightCount = 0;
        rtcSensorFailureCount = 0;
        rtcCycleNumber = 0;
    }

    restoreLampOutputAfterWake();

    if constexpr (CONTINUOUS_TEST_MODE) {
        logLine("Continuous test mode: Deep-sleep is disabled");
        return;
    }

    runMeasurementCycle();
    enterDeepSleep();
}

void loop() {
    if constexpr (CONTINUOUS_TEST_MODE) {
        runMeasurementCycle();
        delay(CONTINUOUS_TEST_INTERVAL_MS);
    }
}
