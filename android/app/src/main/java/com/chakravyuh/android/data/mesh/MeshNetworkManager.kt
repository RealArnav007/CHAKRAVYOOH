package com.chakravyuh.android.data.mesh

import com.chakravyuh.android.domain.model.MeshMessage
import com.chakravyuh.android.domain.model.MeshNode
import kotlinx.coroutines.flow.Flow

interface MeshNetworkManager {
    fun getDiscoveredNodes(): Flow<List<MeshNode>>
    fun getIncomingMessages(): Flow<MeshMessage>
    suspend fun startRelay(): Result<Unit>
    suspend fun stopRelay(): Result<Unit>
    suspend fun sendBroadcast(message: MeshMessage): Result<Unit>
    suspend fun sendDirect(recipientNodeId: String, message: MeshMessage): Result<Unit>
    val localNodeId: String
}
