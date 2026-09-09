package com.pukaar.android.ui.screens.alerts

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.domain.model.CycloneAlert
import com.pukaar.android.domain.repository.AlertRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AlertsState(
    val alerts: List<CycloneAlert> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class AlertsViewModel @Inject constructor(
    private val alertRepository: AlertRepository
) : ViewModel() {

    private val _state = MutableStateFlow(AlertsState(isLoading = true))
    val state: StateFlow<AlertsState> = _state.asStateFlow()

    init {
        loadAlerts()
        observeAlerts()
    }

    fun refresh() {
        loadAlerts()
    }

    private fun loadAlerts() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, error = null) }
            val result = alertRepository.getAlerts()
            result.onSuccess { list ->
                _state.update {
                    it.copy(
                        alerts = list.sortedByDescending { it.issuedAt },
                        isLoading = false,
                        error = null
                    )
                }
            }.onFailure { ex ->
                _state.update {
                    it.copy(
                        isLoading = false,
                        error = ex.message ?: "Failed to fetch alerts"
                    )
                }
            }
        }
    }

    private fun observeAlerts() {
        viewModelScope.launch {
            alertRepository.observeAlertEvents().collect { newAlert ->
                _state.update { current ->
                    val updated = (listOf(newAlert) + current.alerts.filter { it.alertId != newAlert.alertId })
                        .sortedByDescending { it.issuedAt }
                    current.copy(alerts = updated)
                }
            }
        }
    }
}
