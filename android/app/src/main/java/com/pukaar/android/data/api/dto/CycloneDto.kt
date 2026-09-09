package com.pukaar.android.data.api.dto

import com.google.gson.annotations.SerializedName
import com.pukaar.android.domain.model.CycloneData
import com.pukaar.android.domain.model.CyclonePoint
import com.pukaar.android.domain.model.RiskLevel

data class CycloneDto(
    @SerializedName("cyclone_id") val cycloneId: String,
    @SerializedName("name") val name: String,
    @SerializedName("center_lat") val centerLat: Double,
    @SerializedName("center_lon") val centerLon: Double,
    @SerializedName("current_wind_speed_kts") val currentWindSpeedKts: Double,
    @SerializedName("central_pressure_hpa") val centralPressureHpa: Double,
    @SerializedName("r34_km") val r34Km: Double,
    @SerializedName("r50_km") val r50Km: Double,
    @SerializedName("r64_km") val r64Km: Double,
    @SerializedName("landfall_eta") val landfallEtaTimestamp: Long,
    @SerializedName("landfall_probability") val landfallProbability: Double,
    @SerializedName("category") val category: String,
    @SerializedName("risk_level") val riskLevel: String,
    @SerializedName("trajectory") val trajectory: List<CyclonePointDto>?,
    @SerializedName("evacuation_path") val evacuationPath: List<List<Double>>?,
    @SerializedName("last_updated") val lastUpdated: Long
) {
    fun toDomain(): CycloneData {
        val points = trajectory?.map {
            CyclonePoint(it.timestamp, it.latitude, it.longitude, it.windKts, it.label)
        } ?: emptyList()

        val evacPoints = evacuationPath?.mapNotNull {
            if (it.size >= 2) Pair(it[0], it[1]) else null
        } ?: emptyList()

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
            trajectory = points,
            safetyEvacuationPath = evacPoints,
            lastUpdated = lastUpdated
        )
    }
}

data class CyclonePointDto(
    @SerializedName("timestamp") val timestamp: Long,
    @SerializedName("latitude") val latitude: Double,
    @SerializedName("longitude") val longitude: Double,
    @SerializedName("wind_kts") val windKts: Double,
    @SerializedName("label") val label: String
)
