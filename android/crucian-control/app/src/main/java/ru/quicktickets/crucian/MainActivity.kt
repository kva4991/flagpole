package ru.quicktickets.crucian

import android.Manifest
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import android.bluetooth.BluetoothManager
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanFilter
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.ParcelUuid
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewmodel.compose.viewModel
import java.nio.charset.StandardCharsets
import java.util.UUID

private val SERVICE_UUID: UUID = UUID.fromString("d7a10000-4d22-4d86-9287-b5f168000001")
private val STATUS_UUID: UUID = UUID.fromString("d7a10000-4d22-4d86-9287-b5f168000002")
private val CONTROL_UUID: UUID = UUID.fromString("d7a10000-4d22-4d86-9287-b5f168000003")
private val CONFIG_UUID: UUID = UUID.fromString("d7a10000-4d22-4d86-9287-b5f168000004")
private val CCCD_UUID: UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")

class MainActivity : ComponentActivity() {
    private val bleViewModel by lazy { BleViewModel(applicationContext) }

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) {
        bleViewModel.startScanIfPossible(this)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        ensurePermissions()
        setContent {
            MaterialTheme {
                CrucianApp(bleViewModel)
            }
        }
    }

    private fun ensurePermissions() {
        val required = arrayOf(
            Manifest.permission.BLUETOOTH_SCAN,
            Manifest.permission.BLUETOOTH_CONNECT,
            Manifest.permission.ACCESS_FINE_LOCATION,
        )
        val missing = required.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (missing.isNotEmpty()) {
            permissionLauncher.launch(missing.toTypedArray())
        } else {
            bleViewModel.startScanIfPossible(this)
        }
    }
}

enum class WorkMode { AUTO, ON, OFF }

data class UiStatus(
    val connectionText: String = "Не подключено",
    val deviceName: String = "Crucian",
    val lux: Float = 0f,
    val temperature: Float = 0f,
    val humidity: Float = 0f,
    val pressureHpa: Float = 0f,
    val environmentStatus: String = "—",
    val barometerType: String = "—",
    val batteryVolts: Float = 0f,
    val brightnessPercent: Int = 0,
    val mode: WorkMode = WorkMode.AUTO,
    val bleActive: Boolean = true,
    val lastMessage: String = "",
)

class BleViewModel(private val context: Context) : ViewModel() {
    var uiStatus by mutableStateOf(UiStatus())
        private set

    private val bluetoothManager = context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
    private val adapter: BluetoothAdapter? = bluetoothManager.adapter
    private val scanner get() = adapter?.bluetoothLeScanner
    private var gatt: BluetoothGatt? = null
    private var controlCharacteristic: BluetoothGattCharacteristic? = null
    private var configCharacteristic: BluetoothGattCharacteristic? = null

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val device = result.device ?: return
            if (result.scanRecord?.deviceName == "Crucian" || device.name == "Crucian") {
                scanner?.stopScan(this)
                uiStatus = uiStatus.copy(connectionText = "Подключение к ${device.address}")
                gatt = device.connectGatt(context, false, gattCallback, BluetoothDevice.TRANSPORT_LE)
            }
        }
    }

    private val gattCallback = object : BluetoothGattCallback() {
        override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
            if (newState == android.bluetooth.BluetoothProfile.STATE_CONNECTED) {
                uiStatus = uiStatus.copy(connectionText = "Подключено, поиск сервисов")
                gatt.discoverServices()
            } else if (newState == android.bluetooth.BluetoothProfile.STATE_DISCONNECTED) {
                uiStatus = uiStatus.copy(connectionText = "Отключено")
                controlCharacteristic = null
                configCharacteristic = null
            }
        }

        override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
            val service = gatt.getService(SERVICE_UUID) ?: return
            val statusChar = service.getCharacteristic(STATUS_UUID)
            controlCharacteristic = service.getCharacteristic(CONTROL_UUID)
            configCharacteristic = service.getCharacteristic(CONFIG_UUID)
            uiStatus = uiStatus.copy(connectionText = "Готово")
            gatt.setCharacteristicNotification(statusChar, true)
            statusChar.getDescriptor(CCCD_UUID)?.let { descriptor ->
                descriptor.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                gatt.writeDescriptor(descriptor)
            }
            readConfig()
        }

        @Deprecated("Deprecated in API 33")
        override fun onCharacteristicChanged(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic) {
            if (characteristic.uuid == STATUS_UUID) {
                parseStatus(characteristic.value?.toString(StandardCharsets.UTF_8).orEmpty())
            }
        }

        override fun onCharacteristicRead(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            value: ByteArray,
            status: Int,
        ) {
            if (characteristic.uuid == CONFIG_UUID) {
                uiStatus = uiStatus.copy(lastMessage = value.toString(StandardCharsets.UTF_8))
            }
        }
    }

    fun startScanIfPossible(activity: Context) {
        if (adapter?.isEnabled != true) {
            uiStatus = uiStatus.copy(connectionText = "Bluetooth выключен")
            return
        }
        val filters = listOf(ScanFilter.Builder().setDeviceName("Crucian").build())
        val settings = ScanSettings.Builder().setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build()
        scanner?.startScan(filters, settings, scanCallback)
        uiStatus = uiStatus.copy(connectionText = "Поиск устройства Crucian")
    }

    fun sendMode(mode: WorkMode) = writeControl("MODE:${mode.name}")
    fun sendBrightness(percent: Int) = writeControl("BRIGHTNESS:$percent")
    fun sendBleOff() = writeControl("BLE:OFF")
    fun calibrateDay() = writeControl("CALIBRATE:DAY")
    fun calibrateNight() = writeControl("CALIBRATE:NIGHT")
    fun requestStatus() = writeControl("STATUS?")
    fun changePin(oldPin: String, newPin: String) = writeControl("PIN:${oldPin.trim()},${newPin.trim()}")

    private fun readConfig() {
        val char = configCharacteristic ?: return
        gatt?.readCharacteristic(char)
    }

    private fun writeControl(command: String) {
        val char = controlCharacteristic ?: return
        char.value = command.toByteArray(StandardCharsets.UTF_8)
        gatt?.writeCharacteristic(char)
        uiStatus = uiStatus.copy(lastMessage = "→ $command")
    }

    private fun parseStatus(raw: String) {
        // Формат: MODE=AUTO;LUX=12.4;TEMP=25.1;HUM=48.0;PRESS=1013.2;ENV=OK;BARO=BMP280;...
        val map = raw.split(';').mapNotNull { part ->
            val idx = part.indexOf('=')
            if (idx <= 0) null else part.substring(0, idx) to part.substring(idx + 1)
        }.toMap()
        val mode = when (map["MODE"]) {
            "ON" -> WorkMode.ON
            "OFF" -> WorkMode.OFF
            else -> WorkMode.AUTO
        }
        uiStatus = uiStatus.copy(
            lux = map["LUX"]?.toFloatOrNull() ?: uiStatus.lux,
            temperature = map["TEMP"]?.toFloatOrNull() ?: uiStatus.temperature,
            humidity = map["HUM"]?.toFloatOrNull() ?: uiStatus.humidity,
            pressureHpa = map["PRESS"]?.toFloatOrNull() ?: uiStatus.pressureHpa,
            environmentStatus = map["ENV"] ?: uiStatus.environmentStatus,
            barometerType = map["BARO"] ?: uiStatus.barometerType,
            batteryVolts = map["BAT"]?.toFloatOrNull() ?: uiStatus.batteryVolts,
            brightnessPercent = map["BRI"]?.toIntOrNull() ?: uiStatus.brightnessPercent,
            bleActive = map["BLE"] == "1",
            mode = mode,
            lastMessage = raw,
        )
    }
}

@Composable
fun CrucianApp(vm: BleViewModel = viewModel()) {
    val status = vm.uiStatus
    val context = LocalContext.current
    var brightness by remember { mutableIntStateOf(status.brightnessPercent.coerceIn(0, 100)) }
    var oldPin by remember { mutableStateOf("") }
    var newPin by remember { mutableStateOf("") }

    LaunchedEffect(status.brightnessPercent) { brightness = status.brightnessPercent.coerceIn(0, 100) }

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text("Crucian", style = MaterialTheme.typography.headlineMedium)
        Text("Состояние подключения: ${status.connectionText}")
        Text("Освещённость: ${status.lux} лк")
        Text("Температура: ${status.temperature} °C")
        Text("Влажность: ${status.humidity} %")
        Text("Давление: ${status.pressureHpa} гПа")
        Text("Климатические датчики: ${status.environmentStatus}; ${status.barometerType}")
        Text("Напряжение батареи: ${status.batteryVolts} В")
        Text("Яркость: ${status.brightnessPercent} %")
        Text("Последнее сообщение: ${status.lastMessage}")

        Text("Режим")
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            WorkMode.values().forEach { mode ->
                Row {
                    RadioButton(selected = status.mode == mode, onClick = { vm.sendMode(mode) })
                    Text(mode.name)
                }
            }
        }

        Text("Ручная яркость")
        Slider(
            value = brightness.toFloat(),
            onValueChange = { brightness = it.toInt() },
            valueRange = 0f..100f,
        )
        Button(onClick = { vm.sendBrightness(brightness) }) {
            Text("Отправить яркость")
        }

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = vm::calibrateDay) { Text("Калибровать день") }
            Button(onClick = vm::calibrateNight) { Text("Калибровать ночь") }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = vm::requestStatus) { Text("Обновить статус") }
            Button(onClick = vm::sendBleOff) { Text("Выключить BLE") }
        }

        OutlinedTextField(value = oldPin, onValueChange = { oldPin = it }, label = { Text("Старый PIN") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(value = newPin, onValueChange = { newPin = it }, label = { Text("Новый PIN") }, modifier = Modifier.fillMaxWidth())
        Button(onClick = { vm.changePin(oldPin, newPin) }) {
            Text("Сменить PIN")
        }

        TextButton(onClick = { vm.startScanIfPossible(context) }) {
            Text("Повторно сканировать")
        }
    }
}
