package com.pukaar.android.domain.model

data class SosMessage(
    val id: String,
    val senderId: String,
    val senderName: String,
    val latitude: Double,
    val longitude: Double,
    val emergencyType: String, // "MEDICAL", "TRAPPED", "RATIONS", "EVACUATION"
    val victimCount: Int,
    val notes: String,
    val timestamp: Long,
    val hopCount: Int = 0,
    val isEncrypted: Boolean = true,
    val signature: String = "",
    val status: SosStatus = SosStatus.QUEUED_FOR_MESH
)

enum class SosStatus {
    QUEUED_FOR_MESH,
    RELAYED_BY_PEERS,
    RECEIVED_BY_RESCUE,
    ACKNOWLEDGED
}
