package com.pukaar.android.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.pukaar.android.domain.model.MeshPeer

@Entity(tableName = "mesh_peers")
data class MeshPeerEntity(
    @PrimaryKey val peerId: String,
    val alias: String,
    val rssi: Int,
    val hops: Int,
    val isRelayActive: Boolean,
    val lastSeenTimestamp: Long
) {
    fun toDomain(): MeshPeer = MeshPeer(
        peerId = peerId,
        alias = alias,
        rssi = rssi,
        hops = hops,
        isRelayActive = isRelayActive,
        lastSeenTimestamp = lastSeenTimestamp
    )

    companion object {
        fun fromDomain(peer: MeshPeer): MeshPeerEntity = MeshPeerEntity(
            peerId = peer.peerId,
            alias = peer.alias,
            rssi = peer.rssi,
            hops = peer.hops,
            isRelayActive = peer.isRelayActive,
            lastSeenTimestamp = peer.lastSeenTimestamp
        )
    }
}
