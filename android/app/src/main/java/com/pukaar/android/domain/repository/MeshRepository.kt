package com.pukaar.android.domain.repository

import com.pukaar.android.domain.model.MeshPacket
import com.pukaar.android.domain.model.MeshStatus
import com.pukaar.android.domain.model.PacketLogEntry
import kotlinx.coroutines.flow.Flow

interface MeshRepository {
    fun observeMeshStatus(): Flow<MeshStatus>
    suspend fun relayPacket(packet: MeshPacket): Result<Unit>
    fun observePacketLog(): Flow<List<PacketLogEntry>>
}
