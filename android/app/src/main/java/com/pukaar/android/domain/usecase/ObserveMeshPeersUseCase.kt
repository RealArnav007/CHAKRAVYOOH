package com.pukaar.android.domain.usecase

import com.pukaar.android.domain.model.MeshPeer
import com.pukaar.android.domain.repository.MeshRepository
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow

class ObserveMeshPeersUseCase @Inject constructor(
    private val meshRepository: MeshRepository
) {
    operator fun invoke(): Flow<List<MeshPeer>> = meshRepository.getDiscoveredPeers()

    suspend fun startRelay(): Result<Unit> = meshRepository.startMeshRelay()

    suspend fun stopRelay(): Result<Unit> = meshRepository.stopMeshRelay()
}
