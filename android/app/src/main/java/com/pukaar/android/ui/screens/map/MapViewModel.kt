package com.pukaar.android.ui.screens.map

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.domain.model.CycloneData
import com.pukaar.android.domain.model.MeshPeer
import com.pukaar.android.domain.usecase.GetCycloneDataUseCase
import com.pukaar.android.domain.usecase.ObserveMeshPeersUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn

data class MapState(
    val cyclone: CycloneData? = null,
    val peers: List<MeshPeer> = emptyList(),
    val userLat: Double = 19.8135,
    val userLon: Double = 85.8312
)

@HiltViewModel
class MapViewModel @Inject constructor(
    private val getCycloneUseCase: GetCycloneDataUseCase,
    private val observeMeshPeersUseCase: ObserveMeshPeersUseCase
) : ViewModel() {

    val state: StateFlow<MapState> = combine(
        getCycloneUseCase(),
        observeMeshPeersUseCase()
    ) { cyclone, peers ->
        MapState(cyclone = cyclone, peers = peers)
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = MapState()
    )
}
