package com.pukaar.android.data.repository

import com.pukaar.android.data.mesh.MeshManager
import com.pukaar.android.domain.model.MeshPeer
import com.pukaar.android.domain.repository.MeshRepository
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow

@Singleton
class MeshRepositoryImpl @Inject constructor(
    private val meshManager: MeshManager
) : MeshRepository {

    override fun getDiscoveredPeers(): Flow<List<MeshPeer>> {
        return meshManager.getDiscoveredPeers()
    }

    override suspend fun startMeshRelay(): Result<Unit> {
        return meshManager.startMeshRelay()
    }

    override suspend fun stopMeshRelay(): Result<Unit> {
        return meshManager.stopMeshRelay()
    }
}
