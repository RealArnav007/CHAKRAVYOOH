package com.pukaar.android.domain.usecase

import com.pukaar.android.domain.model.Alert
import com.pukaar.android.domain.repository.AlertRepository
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow

class GetAlertsUseCase @Inject constructor(
    private val alertRepository: AlertRepository
) {
    operator fun invoke(): Flow<List<Alert>> = alertRepository.getAlertsStream()

    suspend fun refresh(): Result<Unit> = alertRepository.refreshAlerts()

    suspend fun markAsRead(id: String) = alertRepository.markAlertAsRead(id)
}
