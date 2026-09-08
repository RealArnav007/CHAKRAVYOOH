package com.pukaar.android.domain.model

data class PacketLogEntry(
    val msgId: String,
    val type: MessageType,
    val timestamp: Long,
    val status: PacketLogStatus,
    val transport: MeshTransport
)

enum class PacketLogStatus {
    RECEIVED,
    RELAYED,
    DROPPED_DUPLICATE,
    DROPPED_TTL,
    DROPPED_INVALID_SIG,
    DELIVERED
}
