package com.pukaar.android.ui.screens.map

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.data.websocket.PukaarWebSocketManager
import com.pukaar.android.data.websocket.WsState
import com.pukaar.android.domain.model.CycloneIntelligence
import com.pukaar.android.domain.model.RiskZone
import com.pukaar.android.domain.repository.CycloneEvent
import com.pukaar.android.domain.repository.CycloneRepository
import com.pukaar.android.domain.repository.RiskZoneRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class CycloneMapState(
    val intelligence: CycloneIntelligence? = null,
    val riskZones: List<RiskZone> = emptyList(),
    val selectedForecastHour: Int = 24,
    val isLoading: Boolean = false,
    val webSocketConnected: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class CycloneMapViewModel @Inject constructor(
    private val cycloneRepository: CycloneRepository,
    private val riskZoneRepository: RiskZoneRepository,
    private val webSocketManager: PukaarWebSocketManager
) : ViewModel() {

    private val _state = MutableStateFlow(CycloneMapState(isLoading = true))
    val state: StateFlow<CycloneMapState> = _state.asStateFlow()

    init {
        loadData()
        observeWebSocket()
        observeEvents()
    }

    fun selectForecastHour(hour: Int) {
        _state.update { it.copy(selectedForecastHour = hour) }
    }

    fun refresh() {
        loadData()
    }

    private fun loadData() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, error = null) }

            val cycloneRes = cycloneRepository.getActiveCyclones()
            val zonesRes = riskZoneRepository.getRiskZones()

            val intelligence = cycloneRes.getOrNull()?.firstOrNull()
            val riskZones = zonesRes.getOrDefault(emptyList())

            val error = if (cycloneRes.isFailure && zonesRes.isFailure) {
                cycloneRes.exceptionOrNull()?.message ?: "Failed to load cyclone intelligence"
            } else null

            _state.update {
                it.copy(
                    intelligence = intelligence,
                    riskZones = riskZones,
                    isLoading = false,
                    error = error
                )
            }
        }
    }

    private fun observeWebSocket() {
        viewModelScope.launch {
            webSocketManager.connectionState.collect { wsState ->
                _state.update {
                    it.copy(webSocketConnected = wsState == WsState.CONNECTED)
                }
            }
        }
    }

    private fun observeEvents() {
        viewModelScope.launch {
            cycloneRepository.observeCycloneEvents().collect { event ->
                when (event) {
                    is CycloneEvent.Detected -> {
                        _state.update { it.copy(intelligence = event.intelligence) }
                    }
                    is CycloneEvent.Updated -> {
                        _state.update { it.copy(intelligence = event.intelligence) }
                    }
                    is CycloneEvent.PredictionUpdated -> {
                        _state.update { it.copy(intelligence = event.intelligence) }
                    }
                    is CycloneEvent.RiskUpdated -> {
                        _state.update { it.copy(riskZones = event.zones) }
                    }
                }
            }
        }
    }
}
