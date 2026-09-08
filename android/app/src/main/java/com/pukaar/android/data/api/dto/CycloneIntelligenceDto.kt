package com.pukaar.android.data.api.dto

import com.google.gson.annotations.SerializedName

data class CycloneIntelligenceDto(
    @SerializedName("cyclone_id") val cycloneId: String,
    @SerializedName("timestamp") val timestamp: String,
    @SerializedName("detected") val detected: Boolean,
    @SerializedName("detection_confidence") val detectionConfidence: Double,
    @SerializedName("classification") val classification: ClassificationDto?,
    @SerializedName("intensity") val intensity: IntensityDto?,
    @SerializedName("identification") val identification: IdentificationDto?,
    @SerializedName("prediction") val prediction: PredictionDto?,
    @SerializedName("uncertainty") val uncertainty: UncertaintyDto?,
    @SerializedName("freshness") val freshness: FreshnessDto?,
    @SerializedName("current_position") val currentPosition: LatLngDto?,
    @SerializedName("heading") val heading: String?
)

data class IdentificationDto(
    @SerializedName("storm_name") val stormName: String?,
    @SerializedName("basin") val basin: String?
)

data class ClassificationDto(
    @SerializedName("stage") val stage: String,
    @SerializedName("confidence") val confidence: Double
)

data class IntensityDto(
    @SerializedName("level") val level: String,
    @SerializedName("confidence") val confidence: Double,
    @SerializedName("max_wind_speed_kts") val maxWindSpeedKts: Double?,
    @SerializedName("central_pressure_hpa") val centralPressureHpa: Double?
)

data class PredictionDto(
    @SerializedName("forecast_hours") val forecastHours: Int,
    @SerializedName("confidence") val confidence: Double,
    @SerializedName("predicted_path") val predictedPath: List<PathPointDto>?
)

data class UncertaintyDto(
    @SerializedName("radius_km") val radiusKm: Double
)

data class FreshnessDto(
    @SerializedName("generated_at") val generatedAt: String,
    @SerializedName("valid_until") val validUntil: String
)

data class PathPointDto(
    @SerializedName("forecast_hour") val forecastHour: Int,
    @SerializedName("latitude") val latitude: Double,
    @SerializedName("longitude") val longitude: Double
)

data class LatLngDto(
    @SerializedName("latitude") val latitude: Double,
    @SerializedName("longitude") val longitude: Double
)
