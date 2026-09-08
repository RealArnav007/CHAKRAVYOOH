package com.chakravyuh.android.ui.screens.alerts

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chakravyuh.android.domain.model.Alert
import com.chakravyuh.android.domain.repository.AlertRepository
import com.chakravyuh.android.domain.usecase.GetAlertsUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class AlertsUiState(
    val alerts: List<Alert> = emptyList(),
    val isBroadcasting: Boolean = false
)

@HiltViewModel
class AlertsViewModel @Inject constructor(
    private val getAlertsUseCase: GetAlertsUseCase,
    private val alertRepository: AlertRepository
) : ViewModel() {

    val uiState: StateFlow<AlertsUiState> = getAlertsUseCase()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        ).let { flow ->
            kotlinx.coroutines.flow.map(flow) { alerts ->
                AlertsUiState(alerts = alerts)
            }.stateIn(
                scope = viewModelScope,
                started = SharingStarted.WhileSubscribed(5000),
                initialValue = AlertsUiState()
            )
        }

    fun broadcastAlertViaMesh(alert: Alert) {
        viewModelScope.launch {
            alertRepository.broadcastAlertViaMesh(alert)
        }
    }

    fun markAsRead(alertId: String) {
        viewModelScope.launch {
            alertRepository.markAlertAsRead(alertId)
        }
    }
}
