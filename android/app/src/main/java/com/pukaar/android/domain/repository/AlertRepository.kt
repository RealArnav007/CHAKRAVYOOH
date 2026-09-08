package com.pukaar.android.domain.repository

import com.pukaar.android.domain.model.CycloneAlert
import kotlinx.coroutines.flow.Flow

interface AlertRepository {
    suspend fun getAlerts(): Result<List<CycloneAlert>>
    fun observeAlertEvents(): Flow<CycloneAlert>
}
