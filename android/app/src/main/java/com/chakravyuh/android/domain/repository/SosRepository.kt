package com.chakravyuh.android.domain.repository

import com.chakravyuh.android.domain.model.SosRequest
import kotlinx.coroutines.flow.Flow

interface SosRepository {
    fun getActiveSosStream(): Flow<SosRequest?>
    suspend fun triggerSos(
        latitude: Double,
        longitude: Double,
        emergencyType: String,
        victimCount: Int,
        notes: String
    ): Result<SosRequest>
    suspend fun cancelSos(sosId: String): Result<Unit>
}
