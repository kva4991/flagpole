package ru.superpommelsandflag.crucian

enum class WorkMode { AUTO, ON, OFF }

enum class BlePhase {
    IDLE,
    SCANNING,
    CONNECTING,
    NEGOTIATING_MTU,
    BONDING,
    DISCOVERING_SERVICES,
    SUBSCRIBING,
    READING_CONFIGURATION,
    READY,
    DISCONNECTING,
    ERROR,
}

data class DeviceTelemetry(
    val lux: Float? = null,
    val temperature: Float? = null,
    val humidity: Float? = null,
    val pressureHpa: Float? = null,
    val brightnessPercent: Int = 0,
    val mode: WorkMode = WorkMode.AUTO,
    val bleActive: Boolean = true,
    val lightSensorStatus: String = "—",
    val environmentStatus: String = "—",
    val barometerType: String = "—",
    val commandResult: String = "—",
)

data class DeviceConfiguration(
    val projectName: String = ProjectIdentity.PROJECT_DISPLAY_NAME,
    val bluetoothName: String = ProjectIdentity.BLE_DEVICE_NAME,
    val dayLux: Float? = null,
    val nightLux: Float? = null,
    val factoryPinStillUsed: Boolean? = null,
    val bleWindowMinutes: Int? = null,
)

data class BleUiState(
    val phase: BlePhase = BlePhase.IDLE,
    val message: String = "Не подключено",
    val deviceAddress: String? = null,
    val mtu: Int = 23,
    val telemetry: DeviceTelemetry = DeviceTelemetry(),
    val configuration: DeviceConfiguration = DeviceConfiguration(),
    val lastRawPayload: String = "",
) {
    val ready: Boolean get() = phase == BlePhase.READY
}
