package com.chakravyuh.android.domain.repository

import com.chakravyuh.android.domain.model.Alert
import kotlinx.coroutines.flow.Flow

interface AlertRepository {
    fun getAlertsStream(): Flow<List<Alert>>
    suspend fun refreshAlerts(): Result<Unit>
    suspend fun markAlertAsRead(alertId: String)
    suspend fun broadcastAlertViaMesh(alert: Alert): Result<Unit>
}
