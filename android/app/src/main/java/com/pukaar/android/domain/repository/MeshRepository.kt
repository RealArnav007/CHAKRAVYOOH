package com.pukaar.android.domain.repository

import com.pukaar.android.domain.model.MeshPeer
import kotlinx.coroutines.flow.Flow

interface MeshRepository {
    fun getDiscoveredPeers(): Flow<List<MeshPeer>>
    suspend fun startMeshRelay(): Result<Unit>
    suspend fun stopMeshRelay(): Result<Unit>
}
