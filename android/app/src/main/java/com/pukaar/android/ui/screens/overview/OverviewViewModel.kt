package com.pukaar.android.ui.screens.overview

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.data.websocket.PukaarWebSocketManager
import com.pukaar.android.data.websocket.WsState
import com.pukaar.android.domain.model.CycloneIntelligence
import com.pukaar.android.domain.repository.CycloneEvent
import com.pukaar.android.domain.repository.CycloneRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class OverviewState(
    val intelligence: CycloneIntelligence? = null,
    val isLoading: Boolean = false,
    val webSocketConnected: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class OverviewViewModel @Inject constructor(
    private val cycloneRepository: CycloneRepository,
    private val webSocketManager: PukaarWebSocketManager
) : ViewModel() {

    private val _state = MutableStateFlow(OverviewState(isLoading = true))
    val state: StateFlow<OverviewState> = _state.asStateFlow()

    init {
        loadData()
        observeWebSocket()
        observeEvents()
    }

    fun refresh() {
        loadData()
    }

    private fun loadData() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, error = null) }
            val result = cycloneRepository.getActiveCyclones()
            result.onSuccess { list ->
                _state.update {
                    it.copy(
                        intelligence = list.firstOrNull(),
                        isLoading = false,
                        error = null
                    )
                }
            }.onFailure { ex ->
                _state.update {
                    it.copy(
                        isLoading = false,
                        error = ex.message ?: "Failed to fetch cyclone intelligence"
                    )
                }
            }
        }
    }

    private fun observeWebSocket() {
        viewModelScope.launch {
            webSocketManager.connectionState.collect { wsState ->
                _state.update { it.copy(webSocketConnected = wsState == WsState.CONNECTED) }
            }
        }
    }

    private fun observeEvents() {
        viewModelScope.launch {
            cycloneRepository.observeCycloneEvents().collect { event ->
                when (event) {
                    is CycloneEvent.Detected -> _state.update { it.copy(intelligence = event.intelligence) }
                    is CycloneEvent.Updated -> _state.update { it.copy(intelligence = event.intelligence) }
                    is CycloneEvent.PredictionUpdated -> _state.update { it.copy(intelligence = event.intelligence) }
                    is CycloneEvent.RiskUpdated -> { /* handled on map */ }
                }
            }
        }
    }
}
