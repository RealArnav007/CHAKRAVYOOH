package com.pukaar.android.data.mesh

import com.pukaar.android.domain.model.MeshPeer
import com.pukaar.android.domain.model.SosMessage
import kotlinx.coroutines.flow.Flow

interface MeshManager {
    val localNodeId: String
    fun getDiscoveredPeers(): Flow<List<MeshPeer>>
    fun getIncomingPackets(): Flow<SosMessage>
    suspend fun startMeshRelay(): Result<Unit>
    suspend fun stopMeshRelay(): Result<Unit>
    suspend fun broadcastPacket(message: SosMessage): Result<Unit>
}
