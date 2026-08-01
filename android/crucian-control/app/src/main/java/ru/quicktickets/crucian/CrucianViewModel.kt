package ru.quicktickets.crucian

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel

class CrucianViewModel(context: Context) : ViewModel() {
    var uiState by mutableStateOf(BleUiState())
        private set

    private val client = CrucianBleClient(context) { newState ->
        uiState = newState
    }

    fun startScan() = client.startScan()
    fun disconnect() = client.disconnect()
    fun sendMode(mode: WorkMode) = client.sendCommand("MODE:${mode.name}")
    fun sendBrightness(percent: Int) = client.sendCommand("BRIGHTNESS:${percent.coerceIn(0, 100)}")
    fun sendBleOff() = client.sendCommand("BLE:OFF")
    fun calibrateDay() = client.sendCommand("CALIBRATE:DAY")
    fun calibrateNight() = client.sendCommand("CALIBRATE:NIGHT")
    fun requestStatus() = client.sendCommand("STATUS?")

    fun changePin(oldPin: String, newPin: String) {
        if (!oldPin.matches(Regex("\\d{6}")) || !newPin.matches(Regex("\\d{6}"))) {
            uiState = uiState.copy(message = "Старый и новый PIN должны состоять из 6 цифр")
            return
        }
        client.sendCommand("PIN:$oldPin,$newPin")
    }

    override fun onCleared() {
        client.close()
        super.onCleared()
    }
}
