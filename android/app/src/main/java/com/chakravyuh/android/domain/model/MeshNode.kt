package com.chakravyuh.android.domain.model

/**
 * Domain model representing a peer in the decentralized Bluetooth / Wi-Fi Direct mesh network.
 */
data class MeshNode(
    val nodeId: String,
    val deviceName: String,
    val signalStrengthRssi: Int,
    val hopCount: Int,
    val isRelayActive: Boolean,
    val lastSeenTimestamp: Long,
    val latitude: Double? = null,
    val longitude: Double? = null
)
