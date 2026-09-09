package com.pukaar.android.ui.screens.alerts

// NEVER log: private key bytes, signature bytes in full, decrypted SOS payload content, sender PII
// Safe to log: msgId (truncated), packet type, verification result (VERIFIED/INVALID), timestamp

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.data.crypto.AlertVerificationService
import com.pukaar.android.domain.model.CycloneAlert
import com.pukaar.android.domain.repository.AlertRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import javax.inject.Inject

data class AlertsState(
    val alerts: List<CycloneAlert> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class AlertsViewModel @Inject constructor(
    private val alertRepository: AlertRepository,
    private val alertVerificationService: AlertVerificationService
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
            result.onSuccess { rawList ->
                // Initial display
                val sortedRaw = rawList.sortedByDescending { it.issuedAt }
                _state.update {
                    it.copy(
                        alerts = sortedRaw,
                        isLoading = false,
                        error = null
                    )
                }

                // Cryptographic verification on background coroutine
                val verifiedList = withContext(Dispatchers.Default) {
                    sortedRaw.map { alert ->
                        val status = alertVerificationService.verifyAlert(alert)
                        alert.copy(verificationStatus = status)
                    }
                }

                _state.update { it.copy(alerts = verifiedList) }
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
            alertRepository.observeAlertEvents().collect { incomingAlert ->
                val verifiedAlert = withContext(Dispatchers.Default) {
                    val status = alertVerificationService.verifyAlert(incomingAlert)
                    incomingAlert.copy(verificationStatus = status)
                }

                _state.update { current ->
                    val updated = (listOf(verifiedAlert) + current.alerts.filter { it.alertId != verifiedAlert.alertId })
                        .sortedByDescending { it.issuedAt }
                    current.copy(alerts = updated)
                }
            }
        }
    }
}
