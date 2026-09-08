package com.chakravyuh.android.data.repository

import com.chakravyuh.android.data.api.ChakravyuhApiService
import com.chakravyuh.android.data.local.dao.AlertDao
import com.chakravyuh.android.data.local.entity.AlertEntity
import com.chakravyuh.android.data.mesh.MeshNetworkManager
import com.chakravyuh.android.domain.model.Alert
import com.chakravyuh.android.domain.model.MeshMessage
import com.chakravyuh.android.domain.model.ThreatLevel
import com.chakravyuh.android.domain.repository.AlertRepository
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

@Singleton
class AlertRepositoryImpl @Inject constructor(
    private val alertDao: AlertDao,
    private val apiService: ChakravyuhApiService,
    private val meshManager: MeshNetworkManager
) : AlertRepository {

    override fun getAlertsStream(): Flow<List<Alert>> {
        return alertDao.getAllAlerts().map { list ->
            if (list.isEmpty()) {
                getMockFallbackAlerts()
            } else {
                list.map { it.toDomain() }
            }
        }
    }

    override suspend fun refreshAlerts(): Result<Unit> {
        return try {
            val response = apiService.getAlerts()
            if (response.isSuccessful && response.body() != null) {
                val dtoList = response.body()!!
                alertDao.insertAlerts(dtoList.map { AlertEntity.fromDomain(it.toDomain()) })
                Result.success(Unit)
            } else {
                // Fallback cache seed
                val fallback = getMockFallbackAlerts()
                alertDao.insertAlerts(fallback.map { AlertEntity.fromDomain(it) })
                Result.success(Unit)
            }
        } catch (e: Exception) {
            val fallback = getMockFallbackAlerts()
            alertDao.insertAlerts(fallback.map { AlertEntity.fromDomain(it) })
            Result.success(Unit)
        }
    }

    override suspend fun markAlertAsRead(alertId: String) {
        alertDao.markAsRead(alertId)
    }

    override suspend fun broadcastAlertViaMesh(alert: Alert): Result<Unit> {
        val payload = "ALERT|${alert.id}|${alert.threatLevel.name}|${alert.title}|${alert.actionAdvice}"
        val meshMessage = MeshMessage(
            messageId = UUID.randomUUID().toString(),
            senderNodeId = meshManager.localNodeId,
            payload = payload,
            signatureHex = "",
            timestamp = System.currentTimeMillis(),
            isEmergencySos = alert.threatLevel == ThreatLevel.EXTREME
        )
        return meshManager.sendBroadcast(meshMessage)
    }

    private fun getMockFallbackAlerts(): List<Alert> {
        val now = System.currentTimeMillis()
        return listOf(
            Alert(
                id = "alt_cyclone_landfall_01",
                title = "Extreme Cyclone Threat: Landfall in 6 Hours",
                description = "Severe cyclonic storm approaching coastal sector. Sustained winds exceeding 120 kts expected with 4.5m storm surges.",
                threatLevel = ThreatLevel.EXTREME,
                category = "CYCLONE",
                zoneId = "ZONE_ODISHA_NORTH",
                affectedAreaName = "Puri - Paradip Coastal Belt",
                timestamp = now - 1800000,
                expiresAt = now + 86400000,
                actionAdvice = "Immediately evacuate low-lying sectors. Proceed to cyclone shelter Alpha/Bravo."
            ),
            Alert(
                id = "alt_storm_surge_02",
                title = "High Risk: Inundation Warning",
                description = "Sea water ingress reported in villages within 3km of shoreline.",
                threatLevel = ThreatLevel.HIGH,
                category = "STORM_SURGE",
                zoneId = "ZONE_ODISHA_CENTRAL",
                affectedAreaName = "Astaranga Coastal Reach",
                timestamp = now - 3600000,
                expiresAt = now + 43200000,
                actionAdvice = "Move cattle and essentials to elevated cyclone shelters."
            ),
            Alert(
                id = "alt_power_grid_03",
                title = "Moderate Risk: Grid De-energization",
                description = "Transmission lines proactively suspended to prevent electrical fires during peak gusts.",
                threatLevel = ThreatLevel.MODERATE,
                category = "INFRASTRUCTURE",
                zoneId = "ZONE_ODISHA_ALL",
                affectedAreaName = "Statewide Grid Sub-stations",
                timestamp = now - 7200000,
                expiresAt = now + 172800000,
                actionAdvice = "Rely on solar lanterns, battery packs, and decentralized Bluetooth mesh for communications."
            )
        )
    }
}
