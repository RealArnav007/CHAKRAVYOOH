package com.chakravyuh.android.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.chakravyuh.android.domain.model.CycloneIntelligence
import com.chakravyuh.android.domain.model.ThreatLevel
import com.chakravyuh.android.domain.model.TrackPoint
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

@Entity(tableName = "cyclone_intelligence")
data class CycloneEntity(
    @PrimaryKey
    val cycloneId: String,
    val name: String,
    val centerLat: Double,
    val centerLon: Double,
    val maxSustainedWindKts: Double,
    val currentPressureHpa: Double,
    val r34RadiusKm: Double,
    val r50RadiusKm: Double,
    val r64RadiusKm: Double,
    val estimatedLandfallTime: Long,
    val landfallProbability: Double,
    val category: String,
    val forecastTrackJson: String,
    val threatLevel: String,
    val lastUpdated: Long
) {
    fun toDomain(gson: Gson): CycloneIntelligence {
        val type = object : TypeToken<List<TrackPoint>>() {}.type
        val track: List<TrackPoint> = try {
            gson.fromJson(forecastTrackJson, type) ?: emptyList()
        } catch (e: Exception) {
            emptyList()
        }

        return CycloneIntelligence(
            cycloneId = cycloneId,
            name = name,
            centerLat = centerLat,
            centerLon = centerLon,
            maxSustainedWindKts = maxSustainedWindKts,
            currentPressureHpa = currentPressureHpa,
            r34RadiusKm = r34RadiusKm,
            r50RadiusKm = r50RadiusKm,
            r64RadiusKm = r64RadiusKm,
            estimatedLandfallTime = estimatedLandfallTime,
            landfallProbability = landfallProbability,
            category = category,
            forecastTrack = track,
            threatLevel = ThreatLevel.fromString(threatLevel),
            lastUpdated = lastUpdated
        )
    }

    companion object {
        fun fromDomain(model: CycloneIntelligence, gson: Gson): CycloneEntity {
            return CycloneEntity(
                cycloneId = model.cycloneId,
                name = model.name,
                centerLat = model.centerLat,
                centerLon = model.centerLon,
                maxSustainedWindKts = model.maxSustainedWindKts,
                currentPressureHpa = model.currentPressureHpa,
                r34RadiusKm = model.r34RadiusKm,
                r50RadiusKm = model.r50RadiusKm,
                r64RadiusKm = model.r64RadiusKm,
                estimatedLandfallTime = model.estimatedLandfallTime,
                landfallProbability = model.landfallProbability,
                category = model.category,
                forecastTrackJson = gson.toJson(model.forecastTrack),
                threatLevel = model.threatLevel.name,
                lastUpdated = model.lastUpdated
            )
        }
    }
}
