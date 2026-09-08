package com.chakravyuh.android.domain.repository

import com.chakravyuh.android.domain.model.CycloneIntelligence
import kotlinx.coroutines.flow.Flow

interface CycloneRepository {
    fun getActiveCycloneStream(): Flow<CycloneIntelligence?>
    suspend fun fetchLatestIntelligence(): Result<CycloneIntelligence>
}
