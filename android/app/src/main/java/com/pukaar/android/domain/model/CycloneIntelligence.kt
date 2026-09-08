package com.pukaar.android.domain.model

data class CycloneIntelligence(
    val cycloneId: String,
    val timestamp: String,
    val detected: Boolean,
    val detectionConfidence: Double,
    val classificationStage: CycloneStage,
    val classificationConfidence: Double,
    val intensityLevel: IntensityLevel,
    val intensityConfidence: Double,
    val currentPosition: LatLng,
    val heading: String,
    val forecastHours: Int,
    val predictionConfidence: Double,
    val predictedPath: List<PathPoint>,
    val uncertaintyRadiusKm: Double,
    val generatedAt: String,
    val validUntil: String
)

enum class CycloneStage {
    DEVELOPING_DISTURBANCE,
    TROPICAL_DEPRESSION,
    MATURE_TROPICAL_CYCLONE,
    WEAKENING_SYSTEM,
    POST_TROPICAL_REMNANT
}

enum class IntensityLevel {
    LOW,
    MODERATE,
    HIGH,
    EXTREME
}

data class PathPoint(
    val forecastHour: Int,
    val latitude: Double,
    val longitude: Double
)
