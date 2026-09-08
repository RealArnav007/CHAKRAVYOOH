package com.chakravyuh.android.domain.repository

import com.chakravyuh.android.domain.model.MeshMessage
import com.chakravyuh.android.domain.model.MeshNode
import kotlinx.coroutines.flow.Flow

interface MeshRepository {
    fun getDiscoveredNodes(): Flow<List<MeshNode>>
    fun getMeshMessagesStream(): Flow<List<MeshMessage>>
    suspend fun startMeshRelay(): Result<Unit>
    suspend fun stopMeshRelay(): Result<Unit>
    suspend fun broadcastMessage(content: String, isEmergency: Boolean): Result<MeshMessage>
    suspend fun sendDirectMessage(recipientNodeId: String, content: String): Result<MeshMessage>
}
