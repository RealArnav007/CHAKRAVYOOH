package com.pukaar.android.data.mesh

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.net.wifi.aware.AttachCallback
import android.net.wifi.aware.DiscoverySessionCallback
import android.net.wifi.aware.PeerHandle
import android.net.wifi.aware.SubscribeConfig
import android.net.wifi.aware.SubscribeDiscoverySession
import android.net.wifi.aware.WifiAwareManager
import android.net.wifi.aware.WifiAwareSession
import android.os.Build
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

class WifiAwareMeshReceiver(private val context: Context) {

    companion object {
        const val SERVICE_NAME = "pukaar_mesh_v1"
    }

    private val gson = Gson()
    private val scope = CoroutineScope(Dispatchers.IO)
    private val _incomingPackets = MutableSharedFlow<Pair<MeshPacket, MeshTransport>>(
        extraBufferCapacity = 64,
        onBufferOverflow = BufferOverflow.DROP_OLDEST
    )
    val incomingPackets: SharedFlow<Pair<MeshPacket, MeshTransport>> = _incomingPackets.asSharedFlow()

    private val wifiAwareManager: WifiAwareManager? by lazy {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O &&
            context.packageManager.hasSystemFeature(PackageManager.FEATURE_WIFI_AWARE)) {
            context.getSystemService(Context.WIFI_AWARE_SERVICE) as? WifiAwareManager
        } else {
            null
        }
    }

    private var awareSession: WifiAwareSession? = null
    private var subscribeSession: SubscribeDiscoverySession? = null

    fun start() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val manager = wifiAwareManager ?: return
        if (!manager.isAvailable) return

        if (ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            return
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(context, Manifest.permission.NEARBY_WIFI_DEVICES) != PackageManager.PERMISSION_GRANTED) {
                return
            }
        }

        try {
            manager.attach(object : AttachCallback() {
                override fun onAttached(session: WifiAwareSession) {
                    awareSession = session
                    subscribeToMeshService(session)
                }

                override fun onAttachFailed() {
                    awareSession = null
                }
            }, null)
        } catch (e: SecurityException) {
            // Missing permissions
        } catch (e: Exception) {
            // Failed to attach
        }
    }

    private fun subscribeToMeshService(session: WifiAwareSession) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val config = SubscribeConfig.Builder()
            .setServiceName(SERVICE_NAME)
            .setSubscribeType(SubscribeConfig.SUBSCRIBE_TYPE_PASSIVE)
            .build()

        try {
            session.subscribe(config, object : DiscoverySessionCallback() {
                override fun onSubscribeStarted(session: SubscribeDiscoverySession) {
                    subscribeSession = session
                }

                override fun onMessageReceived(peerHandle: PeerHandle, message: ByteArray) {
                    handleReceivedMessage(message)
                }
            }, null)
        } catch (e: SecurityException) {
            // Missing permissions
        } catch (e: Exception) {
            // Failed to subscribe
        }
    }

    fun stop() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            subscribeSession?.close()
            subscribeSession = null
            awareSession?.close()
            awareSession = null
        }
    }

    private fun handleReceivedMessage(messageBytes: ByteArray) {
        try {
            val jsonString = String(messageBytes, Charsets.UTF_8)
            val packet = gson.fromJson(jsonString, MeshPacket::class.java)
            if (packet != null) {
                emitPacket(packet)
            }
        } catch (e: Exception) {
            // Invalid message
        }
    }

    fun emitPacket(packet: MeshPacket) {
        scope.launch {
            _incomingPackets.emit(Pair(packet, MeshTransport.WIFI_AWARE))
        }
    }
}
