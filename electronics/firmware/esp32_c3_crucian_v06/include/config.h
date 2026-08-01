#pragma once

#include <Arduino.h>
#include <cstdint>

namespace cfg {
inline constexpr char DEVICE_NAME[] = "Crucian";
inline constexpr uint8_t PIN_PWM = 3;
inline constexpr uint8_t PIN_I2C_SDA = 4;
inline constexpr uint8_t PIN_I2C_SCL = 5;
inline constexpr uint8_t PIN_NTC = 1;
inline constexpr uint8_t PWM_CHANNEL = 0;
inline constexpr uint32_t PWM_FREQ_HZ = 500;
inline constexpr uint8_t PWM_RES_BITS = 10;
inline constexpr uint16_t PWM_MAX = (1u << PWM_RES_BITS) - 1u;
inline constexpr uint32_t BLE_IDLE_WINDOW_MS = 60UL * 60UL * 1000UL; // 1 hour
inline constexpr uint32_t DAY_SLEEP_SEC = 120;
inline constexpr uint32_t DAY_RECHECK_MS = 30UL * 1000UL;
inline constexpr uint32_t NIGHT_RECHECK_MS = 30UL * 1000UL;
inline constexpr float DEFAULT_DAY_LUX = 350.0f;
inline constexpr float DEFAULT_NIGHT_LUX = 25.0f;
inline constexpr uint8_t DEFAULT_MANUAL_BRIGHTNESS = 80;
inline constexpr bool PWM_ACTIVE_HIGH = true;
// Публичный код только для первичной настройки. Перед установкой его нужно сменить.
inline constexpr uint32_t FACTORY_SETUP_PIN = 123456;
inline constexpr uint8_t SENSOR_ERROR_LIMIT = 3;
inline constexpr float NTC_FIXED_R = 10000.0f;
inline constexpr float NTC_BETA = 3950.0f;
inline constexpr float NTC_R0 = 10000.0f;
inline constexpr float NTC_T0_K = 298.15f;
}
