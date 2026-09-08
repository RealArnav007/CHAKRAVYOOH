package com.chakravyuh.android.domain.repository

import com.chakravyuh.android.domain.model.EvacuationRoute
import kotlinx.coroutines.flow.Flow

interface EvacuationRepository {
    fun getSafeRoutesStream(currentLat: Double, currentLon: Double): Flow<List<EvacuationRoute>>
    suspend fun calculateEvacuationRoute(originLat: Double, originLon: Double): Result<List<EvacuationRoute>>
}
