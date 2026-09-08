package com.chakravyuh.android.domain.model

/**
 * Encrypted mesh packet transferred via Bluetooth LE / Wi-Fi mesh relays.
 */
data class MeshMessage(
    val messageId: String,
    val senderNodeId: String,
    val recipientNodeId: String? = null, // null for broadcast
    val payload: String,
    val signatureHex: String,
    val timestamp: Long,
    val hopLimit: Int = 5,
    val hopsTraversed: Int = 0,
    val isEmergencySos: Boolean = false,
    val isDelivered: Boolean = false
)
