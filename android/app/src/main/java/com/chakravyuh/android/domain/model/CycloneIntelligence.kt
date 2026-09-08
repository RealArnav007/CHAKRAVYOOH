package com.chakravyuh.android.domain.model

/**
 * Domain representation of AI-forecasted Cyclone Intelligence object.
 */
data class CycloneIntelligence(
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
    val category: String, // e.g. "Category 4", "Very Severe Cyclonic Storm"
    val forecastTrack: List<TrackPoint>,
    val threatLevel: ThreatLevel,
    val lastUpdated: Long
)

data class TrackPoint(
    val timestamp: Long,
    val latitude: Double,
    val longitude: Double,
    val windSpeedKts: Double,
    val intensityCategory: String
)
