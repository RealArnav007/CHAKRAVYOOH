package com.chakravyuh.android.domain.model

/**
 * Domain representation of a high-priority Pukar SOS distress call.
 */
data class SosRequest(
    val sosId: String,
    val userId: String,
    val latitude: Double,
    val longitude: Double,
    val accuracyMeters: Float,
    val emergencyType: String, // "MEDICAL", "TRAPPED", "FOOD_WATER", "GENERAL"
    val victimCount: Int,
    val medicalNotes: String,
    val batteryLevel: Int,
    val timestamp: Long,
    val status: SosStatus = SosStatus.DISPATCHING
)

enum class SosStatus {
    PENDING_MESH_RELAY,
    DISPATCHING,
    ACKNOWLEDGED_BY_RESCUE,
    RESOLVED
}
