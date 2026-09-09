package com.pukaar.android.domain.repository

import com.pukaar.android.domain.model.CycloneIntelligence
import com.pukaar.android.domain.model.RiskZone
import kotlinx.coroutines.flow.Flow

interface CycloneRepository {
    suspend fun getActiveCyclones(): Result<List<CycloneIntelligence>>
    suspend fun getCycloneById(id: String): Result<CycloneIntelligence>
    fun observeCycloneEvents(): Flow<CycloneEvent>
}

sealed class CycloneEvent {
    data class Detected(val intelligence: CycloneIntelligence) : CycloneEvent()
    data class Updated(val intelligence: CycloneIntelligence) : CycloneEvent()
    data class PredictionUpdated(val intelligence: CycloneIntelligence) : CycloneEvent()
    data class RiskUpdated(val zones: List<RiskZone>) : CycloneEvent()
}
