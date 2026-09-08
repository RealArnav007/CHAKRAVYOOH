package com.chakravyuh.android.data.repository

import com.chakravyuh.android.data.local.dao.MeshMessageDao
import com.chakravyuh.android.data.local.entity.MeshMessageEntity
import com.chakravyuh.android.data.mesh.MeshNetworkManager
import com.chakravyuh.android.domain.model.MeshMessage
import com.chakravyuh.android.domain.model.MeshNode
import com.chakravyuh.android.domain.repository.MeshRepository
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch

@Singleton
class MeshRepositoryImpl @Inject constructor(
    private val meshManager: MeshNetworkManager,
    private val meshMessageDao: MeshMessageDao
) : MeshRepository {

    private val scope = CoroutineScope(Dispatchers.IO)

    init {
        // Listen to incoming packets from mesh manager and save to local Room db
        scope.launch {
            meshManager.getIncomingMessages().collect { message ->
                meshMessageDao.insertMessage(MeshMessageEntity.fromDomain(message))
            }
        }
    }

    override fun getDiscoveredNodes(): Flow<List<MeshNode>> {
        return meshManager.getDiscoveredNodes()
    }

    override fun getMeshMessagesStream(): Flow<List<MeshMessage>> {
        return meshMessageDao.getAllMessages().map { list ->
            list.map { it.toDomain() }
        }
    }

    override suspend fun startMeshRelay(): Result<Unit> {
        return meshManager.startRelay()
    }

    override suspend fun stopMeshRelay(): Result<Unit> {
        return meshManager.stopRelay()
    }

    override suspend fun broadcastMessage(
        content: String,
        isEmergency: Boolean
    ): Result<MeshMessage> {
        val msg = MeshMessage(
            messageId = UUID.randomUUID().toString(),
            senderNodeId = meshManager.localNodeId,
            recipientNodeId = null,
            payload = content,
            signatureHex = "",
            timestamp = System.currentTimeMillis(),
            isEmergencySos = isEmergency,
            isDelivered = false
        )
        val res = meshManager.sendBroadcast(msg)
        return if (res.isSuccess) {
            meshMessageDao.insertMessage(MeshMessageEntity.fromDomain(msg.copy(isDelivered = true)))
            Result.success(msg)
        } else {
            Result.failure(res.exceptionOrNull() ?: Exception("Broadcast failed"))
        }
    }

    override suspend fun sendDirectMessage(
        recipientNodeId: String,
        content: String
    ): Result<MeshMessage> {
        val msg = MeshMessage(
            messageId = UUID.randomUUID().toString(),
            senderNodeId = meshManager.localNodeId,
            recipientNodeId = recipientNodeId,
            payload = content,
            signatureHex = "",
            timestamp = System.currentTimeMillis(),
            isEmergencySos = false,
            isDelivered = false
        )
        val res = meshManager.sendDirect(recipientNodeId, msg)
        return if (res.isSuccess) {
            meshMessageDao.insertMessage(MeshMessageEntity.fromDomain(msg.copy(isDelivered = true)))
            Result.success(msg)
        } else {
            Result.failure(res.exceptionOrNull() ?: Exception("Send direct failed"))
        }
    }
}
