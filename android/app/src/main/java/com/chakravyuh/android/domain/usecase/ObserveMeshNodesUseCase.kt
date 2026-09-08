package com.chakravyuh.android.domain.usecase

import com.chakravyuh.android.domain.model.MeshNode
import com.chakravyuh.android.domain.repository.MeshRepository
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow

class ObserveMeshNodesUseCase @Inject constructor(
    private val meshRepository: MeshRepository
) {
    operator fun invoke(): Flow<List<MeshNode>> {
        return meshRepository.getDiscoveredNodes()
    }

    suspend fun startMeshRelay(): Result<Unit> {
        return meshRepository.startMeshRelay()
    }

    suspend fun stopMeshRelay(): Result<Unit> {
        return meshRepository.stopMeshRelay()
    }
}
