package com.pukaar.android.ui.screens.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.domain.model.Alert
import com.pukaar.android.domain.model.CycloneData
import com.pukaar.android.domain.model.MeshPeer
import com.pukaar.android.domain.model.RiskLevel
import com.pukaar.android.domain.usecase.GetAlertsUseCase
import com.pukaar.android.domain.usecase.GetCycloneDataUseCase
import com.pukaar.android.domain.usecase.ObserveMeshPeersUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class HomeState(
    val cyclone: CycloneData? = null,
    val alerts: List<Alert> = emptyList(),
    val peers: List<MeshPeer> = emptyList(),
    val highestRisk: RiskLevel = RiskLevel.EXTREME
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val getCycloneUseCase: GetCycloneDataUseCase,
    private val getAlertsUseCase: GetAlertsUseCase,
    private val observeMeshPeersUseCase: ObserveMeshPeersUseCase
) : ViewModel() {

    val state: StateFlow<HomeState> = combine(
        getCycloneUseCase(),
        getAlertsUseCase(),
        observeMeshPeersUseCase()
    ) { cyclone, alerts, peers ->
        val maxRisk = alerts.maxByOrNull { it.riskLevel.ordinal }?.riskLevel
            ?: cyclone?.riskLevel
            ?: RiskLevel.LOW

        HomeState(
            cyclone = cyclone,
            alerts = alerts,
            peers = peers,
            highestRisk = maxRisk
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = HomeState()
    )

    fun refresh() {
        viewModelScope.launch {
            getCycloneUseCase.refresh()
            getAlertsUseCase.refresh()
        }
    }
}
