package com.pukaar.android.ui.screens.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.data.websocket.PukaarWebSocketManager
import com.pukaar.android.data.websocket.WsState
import com.pukaar.android.domain.model.CycloneAlert
import com.pukaar.android.domain.model.CycloneIntelligence
import com.pukaar.android.domain.model.MeshStatus
import com.pukaar.android.domain.model.RiskLevel
import com.pukaar.android.domain.model.RiskZone
import com.pukaar.android.domain.repository.AlertRepository
import com.pukaar.android.domain.repository.CycloneEvent
import com.pukaar.android.domain.repository.CycloneRepository
import com.pukaar.android.domain.repository.MeshRepository
import com.pukaar.android.domain.repository.RiskZoneRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class HomeState(
    val intelligence: CycloneIntelligence? = null,
    val riskZones: List<RiskZone> = emptyList(),
    val alerts: List<CycloneAlert> = emptyList(),
    val meshStatus: MeshStatus? = null,
    val webSocketConnected: Boolean = false,
    val isAlertDismissed: Boolean = false,
    val isLoading: Boolean = false
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val cycloneRepository: CycloneRepository,
    private val alertRepository: AlertRepository,
    private val riskZoneRepository: RiskZoneRepository,
    private val meshRepository: MeshRepository,
    private val webSocketManager: PukaarWebSocketManager
) : ViewModel() {

    private val _state = MutableStateFlow(HomeState(isLoading = true))
    val state: StateFlow<HomeState> = _state.asStateFlow()

    init {
        loadData()
        observeStreams()
    }

    private fun loadData() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true) }

            val cycloneRes = cycloneRepository.getActiveCyclones()
            val alertsRes = alertRepository.getAlerts()
            val zonesRes = riskZoneRepository.getRiskZones()

            _state.update {
                it.copy(
                    intelligence = cycloneRes.getOrNull()?.firstOrNull(),
                    alerts = alertsRes.getOrDefault(emptyList()),
                    riskZones = zonesRes.getOrDefault(emptyList()),
                    isLoading = false
                )
            }
        }
    }

    private fun observeStreams() {
        // WebSocket state
        viewModelScope.launch {
            webSocketManager.connectionState.collect { ws ->
                _state.update { it.copy(webSocketConnected = ws == WsState.CONNECTED) }
            }
        }

        // Mesh status
        viewModelScope.launch {
            meshRepository.observeMeshStatus().collect { mesh ->
                _state.update { it.copy(meshStatus = mesh) }
            }
        }

        // Live Cyclone events
        viewModelScope.launch {
            cycloneRepository.observeCycloneEvents().collect { event ->
                when (event) {
                    is CycloneEvent.Detected -> _state.update { it.copy(intelligence = event.intelligence) }
                    is CycloneEvent.Updated -> _state.update { it.copy(intelligence = event.intelligence) }
                    is CycloneEvent.PredictionUpdated -> _state.update { it.copy(intelligence = event.intelligence) }
                    is CycloneEvent.RiskUpdated -> _state.update { it.copy(riskZones = event.zones) }
                }
            }
        }
    }

    fun dismissAlert() {
        _state.update { it.copy(isAlertDismissed = true) }
    }
}
