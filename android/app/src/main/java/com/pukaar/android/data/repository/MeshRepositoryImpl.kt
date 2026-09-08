package com.pukaar.android.data.repository

import com.pukaar.android.data.mesh.MeshStatusObserver
import com.pukaar.android.domain.model.MeshPacket
import com.pukaar.android.domain.model.MeshStatus
import com.pukaar.android.domain.model.PacketLogEntry
import com.pukaar.android.domain.repository.MeshRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class MeshRepositoryImpl @Inject constructor(
    private val meshStatusObserver: MeshStatusObserver
) : MeshRepository {

    private val _packetLog = MutableStateFlow<List<PacketLogEntry>>(emptyList())

    override fun observeMeshStatus(): Flow<MeshStatus> {
        return meshStatusObserver.statusFlow
    }

    override suspend fun relayPacket(packet: MeshPacket): Result<Unit> {
        return Result.success(Unit)
    }

    override fun observePacketLog(): Flow<List<PacketLogEntry>> {
        return _packetLog.asStateFlow()
    }

    fun addPacketLogEntry(entry: PacketLogEntry) {
        _packetLog.value = listOf(entry) + _packetLog.value
    }

    fun getPacketLogMutableFlow(): MutableStateFlow<List<PacketLogEntry>> = _packetLog
}
