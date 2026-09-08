package com.chakravyuh.android.domain.model

/**
 * Domain representation of AI-optimized safe evacuation route avoiding storm surges and blocked roads.
 */
data class EvacuationRoute(
    val routeId: String,
    val destinationName: String,
    val shelterCapacity: Int,
    val distanceKm: Double,
    val estimatedMinutes: Int,
    val safetyScore: Double, // 0.0 to 1.0 (1.0 = safest)
    val waypoints: List<Pair<Double, Double>>,
    val roadConditions: String,
    val recommendedTransport: String // "VEHICLE", "FOOT", "AMBULANCE"
)
