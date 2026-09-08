package com.pukaar.android.domain.model

data class IncomingSos(
    val msgId: String,
    val senderHash: String,          // SHA256(senderIdentity).take(8) — anonymized
    val emergencyType: EmergencyType,
    val latitude: Double?,
    val longitude: Double?,
    val message: String?,
    val receivedAt: Long,
    val hopCount: Int,
    val transport: MeshTransport,    // how it arrived: BT or WIFI_AWARE
    val relayStatus: RelayStatus,
    val verificationStatus: VerificationStatus
)

enum class EmergencyType {
    MEDICAL,
    TRAPPED,
    FLOOD,
    OTHER
}

enum class RelayStatus {
    PENDING,
    RELAYED,
    RELAY_FAILED,
    TTL_EXHAUSTED
}
