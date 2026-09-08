package com.chakravyuh.android.domain.usecase

import com.chakravyuh.android.domain.model.MeshMessage
import com.chakravyuh.android.domain.repository.MeshRepository
import javax.inject.Inject

class SendMeshMessageUseCase @Inject constructor(
    private val meshRepository: MeshRepository
) {
    suspend fun broadcast(content: String, isEmergency: Boolean = false): Result<MeshMessage> {
        return meshRepository.broadcastMessage(content, isEmergency)
    }

    suspend fun sendDirect(recipientNodeId: String, content: String): Result<MeshMessage> {
        return meshRepository.sendDirectMessage(recipientNodeId, content)
    }
}
