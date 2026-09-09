package com.pukaar.android.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.pukaar.android.domain.model.CycloneData
import com.pukaar.android.domain.model.CyclonePoint
import com.pukaar.android.domain.model.RiskLevel

@Entity(tableName = "cyclone_state")
data class CycloneEntity(
    @PrimaryKey val cycloneId: String,
    val name: String,
    val centerLat: Double,
    val centerLon: Double,
    val currentWindSpeedKts: Double,
    val centralPressureHpa: Double,
    val r34Km: Double,
    val r50Km: Double,
    val r64Km: Double,
    val landfallEtaTimestamp: Long,
    val landfallProbability: Double,
    val category: String,
    val riskLevel: String,
    val trajectoryJson: String,
    val evacuationPathJson: String,
    val lastUpdated: Long
) {
    fun toDomain(gson: Gson): CycloneData {
        val trajectoryType = object : TypeToken<List<CyclonePoint>>() {}.type
        val evacuationType = object : TypeToken<List<Pair<Double, Double>>>() {}.type

        val trajectory: List<CyclonePoint> = try {
            gson.fromJson(trajectoryJson, trajectoryType) ?: emptyList()
        } catch (e: Exception) {
            emptyList()
        }

        val evacuation: List<Pair<Double, Double>> = try {
            gson.fromJson(evacuationPathJson, evacuationType) ?: emptyList()
        } catch (e: Exception) {
            emptyList()
        }

        return CycloneData(
            cycloneId = cycloneId,
            name = name,
            centerLat = centerLat,
            centerLon = centerLon,
            currentWindSpeedKts = currentWindSpeedKts,
            centralPressureHpa = centralPressureHpa,
            r34Km = r34Km,
            r50Km = r50Km,
            r64Km = r64Km,
            landfallEtaTimestamp = landfallEtaTimestamp,
            landfallProbability = landfallProbability,
            category = category,
            riskLevel = RiskLevel.fromString(riskLevel),
            trajectory = trajectory,
            safetyEvacuationPath = evacuation,
            lastUpdated = lastUpdated
        )
    }

    companion object {
        fun fromDomain(domain: CycloneData, gson: Gson): CycloneEntity {
            return CycloneEntity(
                cycloneId = domain.cycloneId,
                name = domain.name,
                centerLat = domain.centerLat,
                centerLon = domain.centerLon,
                currentWindSpeedKts = domain.currentWindSpeedKts,
                centralPressureHpa = domain.centralPressureHpa,
                r34Km = domain.r34Km,
                r50Km = domain.r50Km,
                r64Km = domain.r64Km,
                landfallEtaTimestamp = domain.landfallEtaTimestamp,
                landfallProbability = domain.landfallProbability,
                category = domain.category,
                riskLevel = domain.riskLevel.name,
                trajectoryJson = gson.toJson(domain.trajectory),
                evacuationPathJson = gson.toJson(domain.safetyEvacuationPath),
                lastUpdated = domain.lastUpdated
            )
        }
    }
}
