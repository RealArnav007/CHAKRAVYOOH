package com.chakravyuh.android.data.repository

import com.chakravyuh.android.data.api.ChakravyuhApiService
import com.chakravyuh.android.data.api.dto.SosPayloadDto
import com.chakravyuh.android.data.mesh.MeshNetworkManager
import com.chakravyuh.android.domain.model.MeshMessage
import com.chakravyuh.android.domain.model.SosRequest
import com.chakravyuh.android.domain.model.SosStatus
import com.chakravyuh.android.domain.repository.SosRepository
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

@Singleton
class SosRepositoryImpl @Inject constructor(
    private val apiService: ChakravyuhApiService,
    private val meshManager: MeshNetworkManager
) : SosRepository {

    private val _activeSos = MutableStateFlow<SosRequest?>(null)
    override fun getActiveSosStream(): Flow<SosRequest?> = _activeSos.asStateFlow()

    override suspend fun triggerSos(
        latitude: Double,
        longitude: Double,
        emergencyType: String,
        victimCount: Int,
        notes: String
    ): Result<SosRequest> {
        val sosId = "SOS_" + UUID.randomUUID().toString().take(8).uppercase()
        val request = SosRequest(
            sosId = sosId,
            userId = meshManager.localNodeId,
            latitude = latitude,
            longitude = longitude,
            accuracyMeters = 8.5f,
            emergencyType = emergencyType,
            victimCount = victimCount,
            medicalNotes = notes,
            batteryLevel = 88,
            timestamp = System.currentTimeMillis(),
            status = SosStatus.DISPATCHING
        )

        _activeSos.value = request

        // 1. Broadcast over decentralized offline Mesh
        val meshPayload = "PUKAR_SOS|$sosId|${request.userId}|$latitude|$longitude|$emergencyType|$victimCount|$notes"
        meshManager.sendBroadcast(
            MeshMessage(
                messageId = UUID.randomUUID().toString(),
                senderNodeId = meshManager.localNodeId,
                payload = meshPayload,
                signatureHex = "",
                timestamp = System.currentTimeMillis(),
                isEmergencySos = true
            )
        )

        // 2. Dispatch via HTTP API if uplink is reachable
        try {
            val dto = SosPayloadDto(
                sosId = sosId,
                userId = request.userId,
                latitude = latitude,
                longitude = longitude,
                emergencyType = emergencyType,
                victimCount = victimCount,
                notes = notes,
                timestamp = request.timestamp
            )
            val res = apiService.sendDistressSignal(dto)
            if (res.isSuccessful) {
                _activeSos.value = request.copy(status = SosStatus.ACKNOWLEDGED_BY_RESCUE)
            }
        } catch (ignored: Exception) {
            // Cellular uplink offline, mesh relay maintains packet propagation
            _activeSos.value = request.copy(status = SosStatus.PENDING_MESH_RELAY)
        }

        return Result.success(request)
    }

    override suspend fun cancelSos(sosId: String): Result<Unit> {
        _activeSos.value = null
        try {
            apiService.cancelDistressSignal(sosId)
        } catch (ignored: Exception) {
        }
        return Result.success(Unit)
    }
}
