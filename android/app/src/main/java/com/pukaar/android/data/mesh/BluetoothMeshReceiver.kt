package com.pukaar.android.data.mesh

import android.Manifest
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanFilter
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.os.ParcelUuid
import androidx.core.content.ContextCompat
import com.google.gson.Gson
import com.pukaar.android.domain.model.MeshPacket
import com.pukaar.android.domain.model.MeshTransport
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.launch
import java.util.UUID

class BluetoothMeshReceiver(private val context: Context) {

    companion object {
        const val SERVICE_UUID_STRING = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
        val SERVICE_UUID: UUID = UUID.fromString(SERVICE_UUID_STRING)
    }

    private val gson = Gson()
    private val scope = CoroutineScope(Dispatchers.IO)
    private val _incomingPackets = MutableSharedFlow<Pair<MeshPacket, MeshTransport>>(
        extraBufferCapacity = 64,
        onBufferOverflow = BufferOverflow.DROP_OLDEST
    )
    val incomingPackets: SharedFlow<Pair<MeshPacket, MeshTransport>> = _incomingPackets.asSharedFlow()

    private val bluetoothAdapter: BluetoothAdapter? by lazy {
        val bluetoothManager = context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
        bluetoothManager?.adapter
    }

    private var isScanning = false

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult?) {
            result?.let { handleScanResult(it) }
        }

        override fun onBatchScanResults(results: MutableList<ScanResult>?) {
            results?.forEach { handleScanResult(it) }
        }

        override fun onScanFailed(errorCode: Int) {
            // Scan failed log or handle
        }
    }

    fun start() {
        if (isScanning) return
        val adapter = bluetoothAdapter ?: return
        if (!adapter.isEnabled) return

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_SCAN) != PackageManager.PERMISSION_GRANTED) {
                return
            }
        }

        val scanner = adapter.bluetoothLeScanner ?: return
        val filter = ScanFilter.Builder()
            .setServiceUuid(ParcelUuid(SERVICE_UUID))
            .build()
        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .build()

        try {
            scanner.startScan(listOf(filter), settings, scanCallback)
            isScanning = true
        } catch (e: SecurityException) {
            // Permission missing
        } catch (e: Exception) {
            // General failure
        }
    }

    fun stop() {
        if (!isScanning) return
        val adapter = bluetoothAdapter ?: return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_SCAN) != PackageManager.PERMISSION_GRANTED) {
                return
            }
        }
        try {
            adapter.bluetoothLeScanner?.stopScan(scanCallback)
        } catch (e: Exception) {
            // Ignore
        } finally {
            isScanning = false
        }
    }

    private fun handleScanResult(result: ScanResult) {
        val record = result.scanRecord ?: return
        val serviceData = record.getServiceData(ParcelUuid(SERVICE_UUID))
        if (serviceData != null && serviceData.isNotEmpty()) {
            try {
                val jsonString = String(serviceData, Charsets.UTF_8)
                val packet = gson.fromJson(jsonString, MeshPacket::class.java)
                if (packet != null) {
                    emitPacket(packet)
                }
            } catch (e: Exception) {
                // Invalid format
            }
        }
    }

    fun emitPacket(packet: MeshPacket) {
        scope.launch {
            _incomingPackets.emit(Pair(packet, MeshTransport.BLUETOOTH))
        }
    }
}
