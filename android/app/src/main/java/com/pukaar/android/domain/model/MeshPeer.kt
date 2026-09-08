package com.pukaar.android.domain.model

data class MeshPeer(
    val peerId: String,
    val alias: String,
    val rssi: Int,
    val hops: Int,
    val isRelayActive: Boolean,
    val lastSeenTimestamp: Long
)
