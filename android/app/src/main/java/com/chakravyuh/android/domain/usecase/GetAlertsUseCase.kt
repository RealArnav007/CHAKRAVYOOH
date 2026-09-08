package com.chakravyuh.android.domain.usecase

import com.chakravyuh.android.domain.model.Alert
import com.chakravyuh.android.domain.repository.AlertRepository
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow

class GetAlertsUseCase @Inject constructor(
    private val alertRepository: AlertRepository
) {
    operator fun invoke(): Flow<List<Alert>> {
        return alertRepository.getAlertsStream()
    }

    suspend fun refresh(): Result<Unit> {
        return alertRepository.refreshAlerts()
    }
}
