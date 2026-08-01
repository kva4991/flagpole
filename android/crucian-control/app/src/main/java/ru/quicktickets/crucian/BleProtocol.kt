package ru.quicktickets.crucian

import java.nio.charset.StandardCharsets
import java.util.UUID

object BleProtocol {
    val SERVICE_UUID: UUID = UUID.fromString("d7a10000-4d22-4d86-9287-b5f168000001")
    val STATUS_UUID: UUID = UUID.fromString("d7a10000-4d22-4d86-9287-b5f168000002")
    val CONTROL_UUID: UUID = UUID.fromString("d7a10000-4d22-4d86-9287-b5f168000003")
    val CONFIG_UUID: UUID = UUID.fromString("d7a10000-4d22-4d86-9287-b5f168000004")
    val CCCD_UUID: UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")

    const val REQUESTED_MTU = 185

    fun decode(value: ByteArray): String = value.toString(StandardCharsets.UTF_8)
    fun encode(value: String): ByteArray = value.toByteArray(StandardCharsets.UTF_8)

    fun parseKeyValuePayload(raw: String): Map<String, String> = raw
        .split(';')
        .mapNotNull { part ->
            val separator = part.indexOf('=')
            if (separator <= 0) null else part.substring(0, separator) to part.substring(separator + 1)
        }
        .toMap()
}
