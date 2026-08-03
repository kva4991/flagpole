package ru.superpommelsandflag.crucian

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanFilter
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.os.Build
import android.os.Handler
import android.os.Looper
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.util.ArrayDeque
import java.util.UUID

/**
 * BLE-клиент с явной машиной состояний и последовательной очередью GATT-операций.
 * Android BLE не допускает надёжного параллельного выполнения нескольких GATT-команд,
 * поэтому каждая операция запускается только после callback предыдущей.
 */
@SuppressLint("MissingPermission")
class CrucianBleClient(
    context: Context,
    private val onStateChanged: (BleUiState) -> Unit,
) {
    private val appContext = context.applicationContext
    private val bluetoothManager = appContext.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
    private val adapter get() = bluetoothManager.adapter
    private val scanner get() = adapter?.bluetoothLeScanner
    private val mainHandler = Handler(Looper.getMainLooper())
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    private var state = BleUiState()
    private var scanCallback: ScanCallback? = null
    private var scanTimeoutJob: Job? = null
    private var connectTimeoutJob: Job? = null
    private var operationTimeoutJob: Job? = null
    private var phaseTimeoutJob: Job? = null
    private var gatt: BluetoothGatt? = null
    private var targetDevice: BluetoothDevice? = null
    private var statusCharacteristic: BluetoothGattCharacteristic? = null
    private var controlCharacteristic: BluetoothGattCharacteristic? = null
    private var configCharacteristic: BluetoothGattCharacteristic? = null
    private var waitingForInitialQueue = false
    private var closed = false

    private sealed interface GattOperation {
        val label: String

        data class WriteDescriptor(
            val descriptor: BluetoothGattDescriptor,
            val value: ByteArray,
            override val label: String,
        ) : GattOperation

        data class ReadCharacteristic(
            val characteristic: BluetoothGattCharacteristic,
            override val label: String,
        ) : GattOperation

        data class WriteCharacteristic(
            val characteristic: BluetoothGattCharacteristic,
            val value: ByteArray,
            override val label: String,
        ) : GattOperation
    }

    private val operationQueue = ArrayDeque<GattOperation>()
    private var activeOperation: GattOperation? = null

    private val bondReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action != BluetoothDevice.ACTION_BOND_STATE_CHANGED) return
            val device = if (Build.VERSION.SDK_INT >= 33) {
                intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE, BluetoothDevice::class.java)
            } else {
                @Suppress("DEPRECATION")
                intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE)
            } ?: return
            if (device.address != targetDevice?.address) return

            when (intent.getIntExtra(BluetoothDevice.EXTRA_BOND_STATE, BluetoothDevice.BOND_NONE)) {
                BluetoothDevice.BOND_BONDED -> onMain {
                    if (state.phase == BlePhase.BONDING) {
                        updatePhase(BlePhase.DISCOVERING_SERVICES, "Сопряжение выполнено, поиск сервисов")
                        discoverServices()
                    }
                }
                BluetoothDevice.BOND_NONE -> onMain {
                    if (state.phase == BlePhase.BONDING) {
                        fail("Сопряжение отменено или PIN не принят")
                    }
                }
            }
        }
    }

    init {
        val filter = IntentFilter(BluetoothDevice.ACTION_BOND_STATE_CHANGED)
        if (Build.VERSION.SDK_INT >= 33) {
            appContext.registerReceiver(bondReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            @Suppress("DEPRECATION")
            appContext.registerReceiver(bondReceiver, filter)
        }
        publish()
    }

    private fun hasConnectPermission(): Boolean =
        Build.VERSION.SDK_INT < 31 || ContextCompat.checkSelfPermission(
            appContext,
            Manifest.permission.BLUETOOTH_CONNECT,
        ) == PackageManager.PERMISSION_GRANTED

    private fun hasScanPermission(): Boolean = when {
        Build.VERSION.SDK_INT >= 31 -> ContextCompat.checkSelfPermission(
            appContext,
            Manifest.permission.BLUETOOTH_SCAN,
        ) == PackageManager.PERMISSION_GRANTED
        else -> ContextCompat.checkSelfPermission(
            appContext,
            Manifest.permission.ACCESS_FINE_LOCATION,
        ) == PackageManager.PERMISSION_GRANTED
    }

    fun startScan() {
        if (closed) return
        if (!hasScanPermission() || !hasConnectPermission()) {
            fail("Нет разрешений Bluetooth")
            return
        }
        if (adapter?.isEnabled != true) {
            fail("Bluetooth выключен")
            return
        }

        resetConnection(closeGatt = true)
        updatePhase(BlePhase.SCANNING, "Поиск ${ProjectIdentity.BLE_DEVICE_NAME}")

        val callback = object : ScanCallback() {
            override fun onScanResult(callbackType: Int, result: ScanResult) {
                val advertisedName = result.scanRecord?.deviceName
                val deviceName = try { result.device.name } catch (_: SecurityException) { null }
                if (advertisedName == ProjectIdentity.BLE_DEVICE_NAME || deviceName == ProjectIdentity.BLE_DEVICE_NAME) {
                    stopScan()
                    connect(result.device)
                }
            }

            override fun onScanFailed(errorCode: Int) {
                onMain {
                    stopScan()
                    fail("Ошибка BLE-сканирования: $errorCode", closeConnection = false)
                }
            }
        }
        scanCallback = callback

        val filters = listOf(
            ScanFilter.Builder().setDeviceName(ProjectIdentity.BLE_DEVICE_NAME).build(),
        )
        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .build()
        scanner?.startScan(filters, settings, callback)

        scanTimeoutJob = scope.launch {
            delay(SCAN_TIMEOUT_MS)
            if (state.phase == BlePhase.SCANNING) {
                stopScan()
                fail("Устройство ${ProjectIdentity.BLE_DEVICE_NAME} не найдено")
            }
        }
    }

    fun disconnect() {
        if (closed) return
        updatePhase(BlePhase.DISCONNECTING, "Отключение")
        stopScan()
        clearOperationQueue()
        phaseTimeoutJob?.cancel()
        gatt?.disconnect()
        scope.launch {
            delay(1500)
            closeGatt()
            updatePhase(BlePhase.IDLE, "Отключено")
        }
    }

    fun sendCommand(command: String) {
        val characteristic = controlCharacteristic
        if (!state.ready || characteristic == null) {
            setMessage("Команда не отправлена: соединение не готово")
            return
        }
        enqueue(
            GattOperation.WriteCharacteristic(
                characteristic,
                BleProtocol.encode(command),
                "Команда $command",
            ),
        )
    }

    fun close() {
        if (closed) return
        closed = true
        stopScan()
        clearOperationQueue()
        connectTimeoutJob?.cancel()
        phaseTimeoutJob?.cancel()
        closeGatt()
        try { appContext.unregisterReceiver(bondReceiver) } catch (_: IllegalArgumentException) { }
        scope.cancel()
    }

    private fun connect(device: BluetoothDevice) {
        if (closed) return
        targetDevice = device
        updateState {
            it.copy(
                phase = BlePhase.CONNECTING,
                message = "Подключение к ${device.address}",
                deviceAddress = device.address,
            )
        }
        gatt = device.connectGatt(appContext, false, gattCallback, BluetoothDevice.TRANSPORT_LE)
        connectTimeoutJob?.cancel()
        connectTimeoutJob = scope.launch {
            delay(CONNECT_TIMEOUT_MS)
            if (state.phase == BlePhase.CONNECTING) {
                fail("Тайм-аут подключения")
            }
        }
    }

    private val gattCallback = object : BluetoothGattCallback() {
        override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
            onMain {
                if (status != BluetoothGatt.GATT_SUCCESS) {
                    fail("Ошибка GATT при подключении: $status")
                    return@onMain
                }
                when (newState) {
                    BluetoothProfile.STATE_CONNECTED -> {
                        connectTimeoutJob?.cancel()
                        updatePhase(BlePhase.NEGOTIATING_MTU, "Подключено, согласование MTU")
                        if (!gatt.requestMtu(BleProtocol.REQUESTED_MTU)) proceedAfterMtu()
                    }
                    BluetoothProfile.STATE_DISCONNECTED -> {
                        val wasDisconnecting = state.phase == BlePhase.DISCONNECTING
                        closeGatt()
                        updatePhase(
                            if (wasDisconnecting) BlePhase.IDLE else BlePhase.ERROR,
                            if (wasDisconnecting) "Отключено" else "Связь потеряна",
                        )
                    }
                }
            }
        }

        override fun onMtuChanged(gatt: BluetoothGatt, mtu: Int, status: Int) {
            onMain {
                if (state.phase != BlePhase.NEGOTIATING_MTU) return@onMain
                updateState { it.copy(mtu = if (status == BluetoothGatt.GATT_SUCCESS) mtu else 23) }
                proceedAfterMtu()
            }
        }

        override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
            onMain {
                if (status != BluetoothGatt.GATT_SUCCESS) {
                    fail("Не удалось получить BLE-сервисы: $status")
                    return@onMain
                }
                val service = gatt.getService(BleProtocol.SERVICE_UUID)
                statusCharacteristic = service?.getCharacteristic(BleProtocol.STATUS_UUID)
                controlCharacteristic = service?.getCharacteristic(BleProtocol.CONTROL_UUID)
                configCharacteristic = service?.getCharacteristic(BleProtocol.CONFIG_UUID)
                if (service == null || statusCharacteristic == null || controlCharacteristic == null || configCharacteristic == null) {
                    fail("Сервис управления или характеристики не найдены")
                    return@onMain
                }
                startInitialGattSequence()
            }
        }

        override fun onDescriptorWrite(gatt: BluetoothGatt, descriptor: BluetoothGattDescriptor, status: Int) {
            onMain { finishOperation(status, BleProtocol.CCCD_UUID, descriptor.uuid) }
        }

        @Deprecated("Legacy callback for Android 12 and older")
        override fun onCharacteristicRead(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            status: Int,
        ) {
            onMain {
                handleCharacteristicRead(characteristic, characteristic.value ?: byteArrayOf(), status)
            }
        }

        override fun onCharacteristicRead(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            value: ByteArray,
            status: Int,
        ) {
            onMain { handleCharacteristicRead(characteristic, value, status) }
        }

        override fun onCharacteristicWrite(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            status: Int,
        ) {
            onMain { finishOperation(status, activeUuid(), characteristic.uuid) }
        }

        @Deprecated("Legacy callback for Android 12 and older")
        override fun onCharacteristicChanged(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic) {
            onMain { handleNotification(characteristic.uuid, characteristic.value ?: byteArrayOf()) }
        }

        override fun onCharacteristicChanged(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            value: ByteArray,
        ) {
            onMain { handleNotification(characteristic.uuid, value) }
        }
    }

    private fun proceedAfterMtu() {
        val device = targetDevice ?: run {
            fail("Устройство потеряно до сопряжения")
            return
        }
        if (device.bondState == BluetoothDevice.BOND_BONDED) {
            updatePhase(BlePhase.DISCOVERING_SERVICES, "Поиск сервисов")
            discoverServices()
        } else {
            updatePhase(BlePhase.BONDING, "Ожидание системного диалога PIN")
            if (!device.createBond()) fail("Не удалось начать сопряжение")
        }
    }

    private fun discoverServices() {
        val localGatt = gatt ?: return
        if (!localGatt.discoverServices()) fail("Не удалось запустить поиск сервисов")
    }

    private fun startInitialGattSequence() {
        val localGatt = gatt ?: return
        val statusChar = statusCharacteristic ?: return
        val configChar = configCharacteristic ?: return
        val cccd = statusChar.getDescriptor(BleProtocol.CCCD_UUID)
        if (cccd == null || !localGatt.setCharacteristicNotification(statusChar, true)) {
            fail("Не удалось подготовить уведомления статуса")
            return
        }
        updatePhase(BlePhase.SUBSCRIBING, "Подписка на уведомления")
        waitingForInitialQueue = true
        enqueue(
            GattOperation.WriteDescriptor(
                cccd,
                BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE,
                "Подписка на статус",
            ),
        )
        enqueue(GattOperation.ReadCharacteristic(configChar, "Чтение конфигурации"))
        enqueue(
            GattOperation.WriteCharacteristic(
                controlCharacteristic!!,
                BleProtocol.encode("STATUS?"),
                "Запрос первого статуса",
            ),
        )
    }

    private fun enqueue(operation: GattOperation) {
        operationQueue.addLast(operation)
        drainQueue()
    }

    private fun drainQueue() {
        if (activeOperation != null || closed) return
        val next = operationQueue.removeFirstOrNull()
        if (next == null) {
            if (waitingForInitialQueue) {
                waitingForInitialQueue = false
                updatePhase(BlePhase.READY, "Готово")
            }
            return
        }
        val localGatt = gatt ?: run {
            fail("GATT закрыт до выполнения ${next.label}")
            return
        }
        activeOperation = next
        operationTimeoutJob?.cancel()
        operationTimeoutJob = scope.launch {
            delay(OPERATION_TIMEOUT_MS)
            if (activeOperation === next) {
                fail("Тайм-аут GATT-операции: ${next.label}")
                clearOperationQueue()
            }
        }

        val started = when (next) {
            is GattOperation.WriteDescriptor -> writeDescriptor(localGatt, next.descriptor, next.value)
            is GattOperation.ReadCharacteristic -> {
                if (next.characteristic.uuid == BleProtocol.CONFIG_UUID) {
                    updatePhase(BlePhase.READING_CONFIGURATION, "Чтение конфигурации")
                }
                localGatt.readCharacteristic(next.characteristic)
            }
            is GattOperation.WriteCharacteristic -> writeCharacteristic(localGatt, next.characteristic, next.value)
        }
        if (!started) {
            operationTimeoutJob?.cancel()
            activeOperation = null
            fail("Не удалось запустить GATT-операцию: ${next.label}")
            clearOperationQueue()
        }
    }

    private fun writeDescriptor(
        gatt: BluetoothGatt,
        descriptor: BluetoothGattDescriptor,
        value: ByteArray,
    ): Boolean = if (Build.VERSION.SDK_INT >= 33) {
        gatt.writeDescriptor(descriptor, value) == BluetoothGatt.GATT_SUCCESS
    } else {
        @Suppress("DEPRECATION")
        run {
            descriptor.value = value
            gatt.writeDescriptor(descriptor)
        }
    }

    private fun writeCharacteristic(
        gatt: BluetoothGatt,
        characteristic: BluetoothGattCharacteristic,
        value: ByteArray,
    ): Boolean = if (Build.VERSION.SDK_INT >= 33) {
        gatt.writeCharacteristic(
            characteristic,
            value,
            BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT,
        ) == BluetoothGatt.GATT_SUCCESS
    } else {
        @Suppress("DEPRECATION")
        run {
            characteristic.writeType = BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
            characteristic.value = value
            gatt.writeCharacteristic(characteristic)
        }
    }

    private fun handleCharacteristicRead(
        characteristic: BluetoothGattCharacteristic,
        value: ByteArray,
        status: Int,
    ) {
        if (status == BluetoothGatt.GATT_SUCCESS) {
            when (characteristic.uuid) {
                BleProtocol.CONFIG_UUID -> parseConfiguration(BleProtocol.decode(value))
                BleProtocol.STATUS_UUID -> parseStatus(BleProtocol.decode(value))
            }
        }
        finishOperation(status, activeUuid(), characteristic.uuid)
    }

    private fun handleNotification(uuid: UUID, value: ByteArray) {
        if (uuid == BleProtocol.STATUS_UUID) parseStatus(BleProtocol.decode(value))
    }

    private fun activeUuid(): UUID? = when (val op = activeOperation) {
        is GattOperation.ReadCharacteristic -> op.characteristic.uuid
        is GattOperation.WriteCharacteristic -> op.characteristic.uuid
        is GattOperation.WriteDescriptor -> op.descriptor.uuid
        null -> null
    }

    private fun finishOperation(status: Int, expectedUuid: UUID?, actualUuid: UUID) {
        val operation = activeOperation ?: return
        if (expectedUuid != null && expectedUuid != actualUuid) return
        operationTimeoutJob?.cancel()
        activeOperation = null
        if (status != BluetoothGatt.GATT_SUCCESS) {
            fail("GATT-операция '${operation.label}' завершилась с кодом $status")
            clearOperationQueue()
            return
        }
        drainQueue()
    }

    private fun clearOperationQueue() {
        operationTimeoutJob?.cancel()
        operationQueue.clear()
        activeOperation = null
        waitingForInitialQueue = false
    }

    private fun parseStatus(raw: String) {
        val values = BleProtocol.parseKeyValuePayload(raw)
        val mode = when (values["MODE"]) {
            "ON" -> WorkMode.ON
            "OFF" -> WorkMode.OFF
            else -> WorkMode.AUTO
        }
        val telemetry = state.telemetry.copy(
            lux = values["LUX"].toNullableFloat(),
            temperature = values["TEMP"].toNullableFloat(),
            humidity = values["HUM"].toNullableFloat(),
            pressureHpa = values["PRESS"].toNullableFloat(),
            brightnessPercent = values["BRI"]?.toIntOrNull() ?: state.telemetry.brightnessPercent,
            bleActive = values["BLE"] != "0",
            lightSensorStatus = values["SENSOR"] ?: state.telemetry.lightSensorStatus,
            environmentStatus = values["ENV"] ?: state.telemetry.environmentStatus,
            barometerType = values["BARO"] ?: state.telemetry.barometerType,
            commandResult = values["RESULT"] ?: state.telemetry.commandResult,
            mode = mode,
        )
        updateState { it.copy(telemetry = telemetry, lastRawPayload = raw) }
    }

    private fun parseConfiguration(raw: String) {
        val values = BleProtocol.parseKeyValuePayload(raw)
        val configuration = state.configuration.copy(
            projectName = values["PROJECT"] ?: state.configuration.projectName,
            bluetoothName = values["NAME"] ?: state.configuration.bluetoothName,
            dayLux = values["DAY"].toNullableFloat(),
            nightLux = values["NIGHT"].toNullableFloat(),
            factoryPinStillUsed = values["PIN_DEFAULT"]?.let { it == "1" },
            bleWindowMinutes = values["WINDOW_MIN"]?.toIntOrNull(),
        )
        updateState { it.copy(configuration = configuration, lastRawPayload = raw) }
    }

    private fun String?.toNullableFloat(): Float? = when (this) {
        null, "NA" -> null
        else -> toFloatOrNull()
    }

    private fun stopScan() {
        scanTimeoutJob?.cancel()
        val callback = scanCallback
        if (callback != null && hasScanPermission()) {
            try { scanner?.stopScan(callback) } catch (_: Exception) { }
        }
        scanCallback = null
    }

    private fun resetConnection(closeGatt: Boolean) {
        stopScan()
        clearOperationQueue()
        connectTimeoutJob?.cancel()
        phaseTimeoutJob?.cancel()
        statusCharacteristic = null
        controlCharacteristic = null
        configCharacteristic = null
        targetDevice = null
        if (closeGatt) closeGatt()
    }

    private fun closeGatt() {
        val localGatt = gatt
        gatt = null
        if (localGatt != null && hasConnectPermission()) {
            try { localGatt.disconnect() } catch (_: Exception) { }
            try { localGatt.close() } catch (_: Exception) { }
        }
    }

    private fun fail(message: String, closeConnection: Boolean = true) {
        stopScan()
        clearOperationQueue()
        connectTimeoutJob?.cancel()
        phaseTimeoutJob?.cancel()
        updateState { it.copy(phase = BlePhase.ERROR, message = message) }
        if (closeConnection) closeGatt()
    }

    private fun setMessage(message: String) {
        updateState { it.copy(message = message) }
    }

    private fun updatePhase(phase: BlePhase, message: String) {
        phaseTimeoutJob?.cancel()
        updateState { it.copy(phase = phase, message = message) }
        phaseTimeoutJob = when (phase) {
            BlePhase.NEGOTIATING_MTU -> scope.launch {
                delay(MTU_TIMEOUT_MS)
                if (state.phase == BlePhase.NEGOTIATING_MTU) {
                    updateState { it.copy(mtu = 23, message = "MTU не подтверждён, продолжаем с 23") }
                    proceedAfterMtu()
                }
            }
            BlePhase.BONDING -> scope.launch {
                delay(BOND_TIMEOUT_MS)
                if (state.phase == BlePhase.BONDING) fail("Тайм-аут сопряжения")
            }
            BlePhase.DISCOVERING_SERVICES -> scope.launch {
                delay(SERVICE_DISCOVERY_TIMEOUT_MS)
                if (state.phase == BlePhase.DISCOVERING_SERVICES) fail("Тайм-аут поиска BLE-сервисов")
            }
            else -> null
        }
    }

    private fun updateState(transform: (BleUiState) -> BleUiState) {
        state = transform(state)
        publish()
    }

    private fun publish() {
        onStateChanged(state)
    }

    private fun onMain(block: () -> Unit) {
        if (Looper.myLooper() == Looper.getMainLooper()) block() else mainHandler.post(block)
    }

    private fun <T> ArrayDeque<T>.removeFirstOrNull(): T? = if (isEmpty()) null else removeFirst()

    companion object {
        private const val SCAN_TIMEOUT_MS = 20_000L
        private const val CONNECT_TIMEOUT_MS = 20_000L
        private const val OPERATION_TIMEOUT_MS = 10_000L
        private const val MTU_TIMEOUT_MS = 8_000L
        private const val BOND_TIMEOUT_MS = 60_000L
        private const val SERVICE_DISCOVERY_TIMEOUT_MS = 15_000L
    }
}
