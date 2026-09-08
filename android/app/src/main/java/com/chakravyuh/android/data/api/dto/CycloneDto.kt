package com.chakravyuh.android.data.api.dto

import com.chakravyuh.android.domain.model.CycloneIntelligence
import com.chakravyuh.android.domain.model.ThreatLevel
import com.chakravyuh.android.domain.model.TrackPoint
import com.google.gson.annotations.SerializedName

data class CycloneDto(
    @SerializedName("cyclone_id") val cycloneId: String,
    @SerializedName("name") val name: String,
    @SerializedName("center_lat") val centerLat: Double,
    @SerializedName("center_lon") val centerLon: Double,
    @SerializedName("max_sustained_wind_kts") val maxSustainedWindKts: Double,
    @SerializedName("current_pressure_hpa") val currentPressureHpa: Double,
    @SerializedName("r34_radius_km") val r34RadiusKm: Double,
    @SerializedName("r50_radius_km") val r50RadiusKm: Double,
    @SerializedName("r64_radius_km") val r64RadiusKm: Double,
    @SerializedName("estimated_landfall_time") val estimatedLandfallTime: Long,
    @SerializedName("landfall_probability") val landfallProbability: Double,
    @SerializedName("category") val category: String,
    @SerializedName("forecast_track") val forecastTrack: List<TrackPointDto>?,
    @SerializedName("threat_level") val threatLevel: String,
    @SerializedName("last_updated") val lastUpdated: Long
) {
    fun toDomain(): CycloneIntelligence {
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
            forecastTrack = forecastTrack?.map { it.toDomain() } ?: emptyList(),
            threatLevel = ThreatLevel.fromString(threatLevel),
            lastUpdated = lastUpdated
        )
    }
}

data class TrackPointDto(
    @SerializedName("timestamp") val timestamp: Long,
    @SerializedName("latitude") val latitude: Double,
    @SerializedName("longitude") val longitude: Double,
    @SerializedName("wind_speed_kts") val windSpeedKts: Double,
    @SerializedName("intensity_category") val intensityCategory: String
) {
    fun toDomain(): TrackPoint {
        return TrackPoint(
            timestamp = timestamp,
            latitude = latitude,
            longitude = longitude,
            windSpeedKts = windSpeedKts,
            intensityCategory = intensityCategory
        )
    }
}
