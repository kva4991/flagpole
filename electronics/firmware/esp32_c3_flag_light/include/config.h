#pragma once

#include <Arduino.h>

namespace FlagLightConfig {

// ESP32-C3 SuperMini Plus: choose ordinary GPIOs, avoiding strapping pins 2, 8 and 9.
inline constexpr uint8_t PIN_LAMP_CONTROL = 3;
inline constexpr uint8_t PIN_I2C_SDA = 4;
inline constexpr uint8_t PIN_I2C_SCL = 5;

// Most PC817 + LR7843 modules are activated by a HIGH input.
// Change to false if the received module is active-low.
inline constexpr bool LAMP_ACTIVE_HIGH = true;

// Wake up once every two minutes.
inline constexpr uint32_t SLEEP_SECONDS = 120;

// Starting values. The optical tunnel attenuates light, so calibrate these
// values on the finished cap after installation.
inline constexpr float LUX_TURN_ON = 8.0F;
inline constexpr float LUX_TURN_OFF = 25.0F;

// 3 dark readings = about 6 minutes before turning on.
// 5 bright readings = about 10 minutes before turning off.
inline constexpr uint8_t DARK_CONFIRMATIONS = 3;
inline constexpr uint8_t LIGHT_CONFIRMATIONS = 5;

// After several consecutive sensor failures, switch the lamp off safely.
inline constexpr uint8_t SENSOR_FAILURE_LIMIT = 3;

// Median filter settings.
inline constexpr uint8_t LUX_SAMPLE_COUNT = 7; // must be odd
inline constexpr uint16_t SAMPLE_PAUSE_MS = 120;

// Set true while commissioning. In normal operation set false.
inline constexpr bool ENABLE_SERIAL_LOG = true;

// Bench mode: no deep sleep, repeat measurements every 5 seconds.
// Keep false for installation on the flagpole.
inline constexpr bool CONTINUOUS_TEST_MODE = false;
inline constexpr uint32_t CONTINUOUS_TEST_INTERVAL_MS = 5000;

} // namespace FlagLightConfig
