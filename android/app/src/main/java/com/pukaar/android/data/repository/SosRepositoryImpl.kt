package com.pukaar.android.data.repository

import com.pukaar.android.data.api.PukaarApiService
import com.pukaar.android.data.api.dto.SosDispatchDto
import com.pukaar.android.data.demo.DemoDataGenerator
import com.pukaar.android.data.local.dao.SosDao
import com.pukaar.android.data.local.entity.SosEntity
import com.pukaar.android.data.mesh.MeshManager
import com.pukaar.android.domain.model.SosMessage
import com.pukaar.android.domain.model.SosStatus
import com.pukaar.android.domain.repository.SosRepository
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch

@Singleton
class SosRepositoryImpl @Inject constructor(
    private val sosDao: SosDao,
    private val meshManager: MeshManager,
    private val apiService: PukaarApiService
) : SosRepository {

    private val scope = CoroutineScope(Dispatchers.IO)
    private val _outgoingSos = MutableStateFlow<SosMessage?>(null)

    init {
        // Populate initial demo inbox if empty
        scope.launch {
            DemoDataGenerator.generateInitialSosInbox().forEach {
                sosDao.insertSos(SosEntity.fromDomain(it))
            }

            // Collect mesh packets
            meshManager.getIncomingPackets().collect { incoming ->
                sosDao.insertSos(SosEntity.fromDomain(incoming))
            }
        }
    }

    override fun getSosInboxStream(): Flow<List<SosMessage>> {
        return sosDao.getAllSosMessages().map { list ->
            list.map { it.toDomain() }
        }
    }

    override fun getActiveOutgoingSosStream(): Flow<SosMessage?> = _outgoingSos.asStateFlow()

    override suspend fun sendEmergencySos(
        latitude: Double,
        longitude: Double,
        emergencyType: String,
        victimCount: Int,
        notes: String
    ): Result<SosMessage> {
        val sosId = "PUKAAR_SOS_" + UUID.randomUUID().toString().take(6).uppercase()
        val sosMessage = SosMessage(
            id = sosId,
            senderId = meshManager.localNodeId,
            senderName = "Citizen Responder",
            latitude = latitude,
            longitude = longitude,
            emergencyType = emergencyType,
            victimCount = victimCount,
            notes = notes,
            timestamp = System.currentTimeMillis(),
            hopCount = 0,
            status = SosStatus.QUEUED_FOR_MESH
        )

        _outgoingSos.value = sosMessage
        sosDao.insertSos(SosEntity.fromDomain(sosMessage))

        // 1. Mesh Broadcast
        meshManager.broadcastPacket(sosMessage)

        // 2. HTTP Dispatch (if uplink reachable)
        try {
            val dto = SosDispatchDto(
                sosId = sosId,
                senderId = sosMessage.senderId,
                senderName = sosMessage.senderName,
                latitude = latitude,
                longitude = longitude,
                emergencyType = emergencyType,
                victimCount = victimCount,
                notes = notes,
                signature = sosMessage.signature,
                timestamp = sosMessage.timestamp
            )
            val res = apiService.dispatchSos(dto)
            if (res.isSuccessful) {
                val updated = sosMessage.copy(status = SosStatus.RECEIVED_BY_RESCUE)
                _outgoingSos.value = updated
                sosDao.insertSos(SosEntity.fromDomain(updated))
            }
        } catch (ignored: Exception) {
            // Relies on offline mesh relay
        }

        return Result.success(sosMessage)
    }

    override suspend fun cancelSos(sosId: String): Result<Unit> {
        _outgoingSos.value = null
        return Result.success(Unit)
    }
}
