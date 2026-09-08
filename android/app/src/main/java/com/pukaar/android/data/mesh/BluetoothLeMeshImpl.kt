package com.pukaar.android.data.mesh

import android.content.Context
import com.pukaar.android.data.crypto.PukaarCryptoManager
import com.pukaar.android.data.demo.DemoDataGenerator
import com.pukaar.android.domain.model.MeshPeer
import com.pukaar.android.domain.model.SosMessage
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

@Singleton
class BluetoothLeMeshImpl @Inject constructor(
    @ApplicationContext private val context: Context,
    private val cryptoManager: PukaarCryptoManager
) : MeshManager {

    private val scope = CoroutineScope(Dispatchers.IO)
    override val localNodeId: String = "pukaar_node_" + UUID.randomUUID().toString().take(6)

    private val _discoveredPeers = MutableStateFlow<List<MeshPeer>>(DemoDataGenerator.generatePeers())
    override fun getDiscoveredPeers(): Flow<List<MeshPeer>> = _discoveredPeers.asStateFlow()

    private val _incomingPackets = MutableSharedFlow<SosMessage>(extraBufferCapacity = 64)
    override fun getIncomingPackets(): Flow<SosMessage> = _incomingPackets.asSharedFlow()

    private var isRelayRunning = false

    override suspend fun startMeshRelay(): Result<Unit> {
        isRelayRunning = true
        scope.launch {
            while (isRelayRunning) {
                delay(10000)
                val peers = _discoveredPeers.value.map {
                    it.copy(lastSeenTimestamp = System.currentTimeMillis())
                }
                _discoveredPeers.value = peers
            }
        }
        return Result.success(Unit)
    }

    override suspend fun stopMeshRelay(): Result<Unit> {
        isRelayRunning = false
        return Result.success(Unit)
    }

    override suspend fun broadcastPacket(message: SosMessage): Result<Unit> {
        val signature = cryptoManager.sign("${message.id}:${message.latitude}:${message.longitude}")
        val signedMessage = message.copy(signature = signature)
        _incomingPackets.emit(signedMessage)
        return Result.success(Unit)
    }
}
