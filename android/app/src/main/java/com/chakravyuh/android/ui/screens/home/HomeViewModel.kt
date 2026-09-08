package com.chakravyuh.android.ui.screens.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chakravyuh.android.domain.model.Alert
import com.chakravyuh.android.domain.model.CycloneIntelligence
import com.chakravyuh.android.domain.model.MeshNode
import com.chakravyuh.android.domain.model.ThreatLevel
import com.chakravyuh.android.domain.usecase.GetAlertsUseCase
import com.chakravyuh.android.domain.usecase.GetCycloneIntelligenceUseCase
import com.chakravyuh.android.domain.usecase.ObserveMeshNodesUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class HomeUiState(
    val cyclone: CycloneIntelligence? = null,
    val alerts: List<Alert> = emptyList(),
    val meshNodes: List<MeshNode> = emptyList(),
    val currentThreatLevel: ThreatLevel = ThreatLevel.EXTREME,
    val isLoading: Boolean = false
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val getCycloneUseCase: GetCycloneIntelligenceUseCase,
    private val getAlertsUseCase: GetAlertsUseCase,
    private val observeMeshNodesUseCase: ObserveMeshNodesUseCase
) : ViewModel() {

    val uiState: StateFlow<HomeUiState> = combine(
        getCycloneUseCase(),
        getAlertsUseCase(),
        observeMeshNodesUseCase()
    ) { cyclone, alerts, meshNodes ->
        val maxThreat = alerts.maxByOrNull { it.threatLevel.ordinal }?.threatLevel
            ?: cyclone?.threatLevel
            ?: ThreatLevel.NORMAL

        HomeUiState(
            cyclone = cyclone,
            alerts = alerts,
            meshNodes = meshNodes,
            currentThreatLevel = maxThreat,
            isLoading = false
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = HomeUiState(isLoading = true)
    )

    fun refresh() {
        viewModelScope.launch {
            getCycloneUseCase.refresh()
            getAlertsUseCase.refresh()
        }
    }
}
