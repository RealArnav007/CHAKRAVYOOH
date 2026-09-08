package com.pukaar.android.domain.model

data class MeshPacket(
    val msgId: String,
    val messageType: MessageType,
    val createdAt: String,
    val ttl: Int,
    val hops: Int,
    val priority: MeshPriority,
    val senderIdentity: String,
    val signature: String,
    val encryptedPayload: String
)

enum class MessageType {
    CYCLONE_WARNING,
    SOS,
    RELAY,
    INFORMATIONAL
}

enum class MeshPriority {
    P0,
    P1,
    P2,
    P3
}
