package com.pukaar.android.data.demo

import com.pukaar.android.data.local.UserPreferences
import com.pukaar.android.domain.model.CycloneAlert
import com.pukaar.android.domain.model.CycloneIntelligence
import com.pukaar.android.domain.model.IncomingSos
import com.pukaar.android.domain.model.MeshPacket
import com.pukaar.android.domain.model.MeshStatus
import com.pukaar.android.domain.model.PacketLogEntry
import com.pukaar.android.domain.model.RelayStatus
import com.pukaar.android.domain.model.RiskZone
import com.pukaar.android.domain.model.SosRequest
import com.pukaar.android.domain.repository.AlertRepository
import com.pukaar.android.domain.repository.CycloneEvent
import com.pukaar.android.domain.repository.CycloneRepository
import com.pukaar.android.domain.repository.MeshRepository
import com.pukaar.android.domain.repository.RiskZoneRepository
import com.pukaar.android.domain.repository.SosRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DemoModeRepository @Inject constructor(
    private val realCycloneRepo: CycloneRepository,
    private val realAlertRepo: AlertRepository,
    private val realRiskZoneRepo: RiskZoneRepository,
    private val realMeshRepo: MeshRepository,
    private val realSosRepo: SosRepository,
    private val userPreferences: UserPreferences
) : CycloneRepository, AlertRepository, RiskZoneRepository, MeshRepository, SosRepository {

    suspend fun isDemoMode(): Boolean {
        return try {
            userPreferences.demoMode.first()
        } catch (e: Exception) {
            false
        }
    }

    // CycloneRepository
    override suspend fun getActiveCyclones(): Result<List<CycloneIntelligence>> {
        return if (isDemoMode()) {
            Result.success(listOf(DemoDataProvider.getCycloneIntelligence()))
        } else {
            realCycloneRepo.getActiveCyclones()
        }
    }

    override suspend fun getCycloneById(id: String): Result<CycloneIntelligence> {
        return if (isDemoMode()) {
            Result.success(DemoDataProvider.getCycloneIntelligence())
        } else {
            realCycloneRepo.getCycloneById(id)
        }
    }

    override fun observeCycloneEvents(): Flow<CycloneEvent> = flow {
        if (isDemoMode()) {
            emit(CycloneEvent.Detected(DemoDataProvider.getCycloneIntelligence()))
            emit(CycloneEvent.RiskUpdated(DemoDataProvider.getRiskZones()))
        } else {
            realCycloneRepo.observeCycloneEvents().collect { emit(it) }
        }
    }

    // AlertRepository
    override suspend fun getAlerts(): Result<List<CycloneAlert>> {
        return if (isDemoMode()) {
            Result.success(DemoDataProvider.getAlerts())
        } else {
            realAlertRepo.getAlerts()
        }
    }

    override fun observeAlertEvents(): Flow<CycloneAlert> = flow {
        if (isDemoMode()) {
            emit(DemoDataProvider.getAlert())
        } else {
            realAlertRepo.observeAlertEvents().collect { emit(it) }
        }
    }

    // RiskZoneRepository
    override suspend fun getRiskZones(): Result<List<RiskZone>> {
        return if (isDemoMode()) {
            Result.success(DemoDataProvider.getRiskZones())
        } else {
            realRiskZoneRepo.getRiskZones()
        }
    }

    // MeshRepository
    override fun observeMeshStatus(): Flow<MeshStatus> = flow {
        if (isDemoMode()) {
            emit(DemoDataProvider.getMeshStatus())
        } else {
            realMeshRepo.observeMeshStatus().collect { emit(it) }
        }
    }

    override suspend fun relayPacket(packet: MeshPacket): Result<Unit> {
        return if (isDemoMode()) {
            Result.success(Unit)
        } else {
            realMeshRepo.relayPacket(packet)
        }
    }

    override fun observePacketLog(): Flow<List<PacketLogEntry>> = flow {
        if (isDemoMode()) {
            emit(emptyList())
        } else {
            realMeshRepo.observePacketLog().collect { emit(it) }
        }
    }

    // SosRepository
    override suspend fun sendSos(request: SosRequest): Result<String> {
        return if (isDemoMode()) {
            Result.success("SOS-DEMO-SENT-OK")
        } else {
            realSosRepo.sendSos(request)
        }
    }

    override fun observeIncomingSos(): Flow<List<IncomingSos>> = flow {
        if (isDemoMode()) {
            emit(DemoDataProvider.getIncomingSosList())
        } else {
            realSosRepo.observeIncomingSos().collect { emit(it) }
        }
    }

    override suspend fun getInboxSnapshot(): List<IncomingSos> {
        return if (isDemoMode()) {
            DemoDataProvider.getIncomingSosList()
        } else {
            realSosRepo.getInboxSnapshot()
        }
    }

    override suspend fun updateRelayStatus(msgId: String, status: RelayStatus) {
        if (!isDemoMode()) {
            realSosRepo.updateRelayStatus(msgId, status)
        }
    }
}
