package com.pukaar.android.domain.repository

import com.pukaar.android.domain.model.CycloneData
import kotlinx.coroutines.flow.Flow

interface CycloneRepository {
    fun getCycloneStream(): Flow<CycloneData?>
    suspend fun refreshCycloneData(): Result<CycloneData>
}
