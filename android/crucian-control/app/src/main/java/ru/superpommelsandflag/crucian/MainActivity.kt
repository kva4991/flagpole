package ru.superpommelsandflag.crucian

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat

class MainActivity : ComponentActivity() {
    private val bleViewModel by lazy { CrucianViewModel(applicationContext) }

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) { result ->
        if (result.values.all { it }) bleViewModel.startScan()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                ProjectControlScreen(bleViewModel)
            }
        }
        ensurePermissionsAndScan()
    }

    private fun ensurePermissionsAndScan() {
        val permissions = if (Build.VERSION.SDK_INT >= 31) {
            arrayOf(Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT)
        } else {
            arrayOf(Manifest.permission.ACCESS_FINE_LOCATION)
        }
        val missing = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (missing.isEmpty()) bleViewModel.startScan() else permissionLauncher.launch(missing.toTypedArray())
    }
}

@Composable
fun ProjectControlScreen(vm: CrucianViewModel) {
    val state = vm.uiState
    var brightness by remember { mutableIntStateOf(state.telemetry.brightnessPercent.coerceIn(0, 100)) }
    var oldPin by remember { mutableStateOf("") }
    var newPin by remember { mutableStateOf("") }

    LaunchedEffect(state.telemetry.brightnessPercent) {
        brightness = state.telemetry.brightnessPercent.coerceIn(0, 100)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(ProjectIdentity.PROJECT_DISPLAY_NAME, style = MaterialTheme.typography.headlineMedium)
        Text("BLE-имя: ${ProjectIdentity.BLE_DEVICE_NAME}")
        Text("Этап: ${state.phase}")
        Text("Состояние: ${state.message}")
        state.deviceAddress?.let { Text("Адрес: $it") }
        Text("MTU: ${state.mtu}")

        TelemetryText("Освещённость", state.telemetry.lux, "лк")
        TelemetryText("Температура", state.telemetry.temperature, "°C")
        TelemetryText("Влажность", state.telemetry.humidity, "%")
        TelemetryText("Давление", state.telemetry.pressureHpa, "гПа")
        Text("Датчик света: ${state.telemetry.lightSensorStatus}")
        Text("Климатический модуль: ${state.telemetry.environmentStatus}; ${state.telemetry.barometerType}")
        Text("Яркость: ${state.telemetry.brightnessPercent} %")
        Text("Результат команды: ${state.telemetry.commandResult}")

        state.configuration.dayLux?.let { Text("Порог дня: $it лк") }
        state.configuration.nightLux?.let { Text("Порог ночи: $it лк") }
        state.configuration.factoryPinStillUsed?.let {
            Text(if (it) "Используется заводской PIN — перед установкой смените его" else "Заводской PIN уже заменён")
        }

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = vm::startScan, enabled = state.phase != BlePhase.SCANNING) {
                Text("Найти устройство")
            }
            Button(onClick = vm::disconnect, enabled = state.phase != BlePhase.IDLE) {
                Text("Отключиться")
            }
        }

        Text("Режим")
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            WorkMode.entries.forEach { mode ->
                Row {
                    RadioButton(
                        selected = state.telemetry.mode == mode,
                        onClick = { vm.sendMode(mode) },
                        enabled = state.ready,
                    )
                    Text(mode.name)
                }
            }
        }

        Text("Ручная яркость")
        Slider(
            value = brightness.toFloat(),
            onValueChange = { brightness = it.toInt() },
            valueRange = 0f..100f,
            enabled = state.ready,
        )
        Button(onClick = { vm.sendBrightness(brightness) }, enabled = state.ready) {
            Text("Установить яркость")
        }

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = vm::calibrateDay, enabled = state.ready) { Text("Текущий свет = день") }
            Button(onClick = vm::calibrateNight, enabled = state.ready) { Text("Текущий свет = ночь") }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = vm::requestStatus, enabled = state.ready) { Text("Обновить статус") }
            Button(onClick = vm::sendBleOff, enabled = state.ready) { Text("Выключить BLE") }
        }

        Text("Смена PIN отзовёт старые BLE-авторизации. После команды потребуется новое сопряжение.")
        OutlinedTextField(
            value = oldPin,
            onValueChange = { oldPin = it.filter(Char::isDigit).take(6) },
            label = { Text("Старый PIN") },
            visualTransformation = PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth(),
            enabled = state.ready,
        )
        OutlinedTextField(
            value = newPin,
            onValueChange = { newPin = it.filter(Char::isDigit).take(6) },
            label = { Text("Новый PIN") },
            visualTransformation = PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth(),
            enabled = state.ready,
        )
        Button(onClick = { vm.changePin(oldPin, newPin) }, enabled = state.ready) {
            Text("Сменить PIN")
        }

        if (state.lastRawPayload.isNotBlank()) {
            Text("Последний пакет: ${state.lastRawPayload}", style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable
private fun TelemetryText(label: String, value: Float?, unit: String) {
    Text("$label: ${value?.let { String.format("%.1f", it) } ?: "—"} $unit")
}
