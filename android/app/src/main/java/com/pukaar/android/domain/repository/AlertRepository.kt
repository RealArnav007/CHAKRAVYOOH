package com.pukaar.android.domain.repository

import com.pukaar.android.domain.model.Alert
import kotlinx.coroutines.flow.Flow

interface AlertRepository {
    fun getAlertsStream(): Flow<List<Alert>>
    suspend fun refreshAlerts(): Result<Unit>
    suspend fun markAlertAsRead(alertId: String)
}
