package com.pukaar.android.domain.repository

import com.pukaar.android.domain.model.SosMessage
import kotlinx.coroutines.flow.Flow

interface SosRepository {
    fun getSosInboxStream(): Flow<List<SosMessage>>
    fun getActiveOutgoingSosStream(): Flow<SosMessage?>
    suspend fun sendEmergencySos(
        latitude: Double,
        longitude: Double,
        emergencyType: String,
        victimCount: Int,
        notes: String
    ): Result<SosMessage>
    suspend fun cancelSos(sosId: String): Result<Unit>
}
