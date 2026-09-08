package com.chakravyuh.android.ui.screens.map

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chakravyuh.android.domain.model.CycloneIntelligence
import com.chakravyuh.android.domain.model.EvacuationRoute
import com.chakravyuh.android.domain.model.MeshNode
import com.chakravyuh.android.domain.usecase.GetCycloneIntelligenceUseCase
import com.chakravyuh.android.domain.usecase.GetEvacuationRoutesUseCase
import com.chakravyuh.android.domain.usecase.ObserveMeshNodesUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn

data class MapUiState(
    val cyclone: CycloneIntelligence? = null,
    val routes: List<EvacuationRoute> = emptyList(),
    val meshNodes: List<MeshNode> = emptyList(),
    val userLatitude: Double = 19.8135,
    val userLongitude = 85.8312,
    val selectedLayer: MapLayer = MapLayer.ALL
)

enum class MapLayer {
    ALL, CYCLONE_WIND, EVACUATION_ROUTES, MESH_NODES
}

@HiltViewModel
class MapViewModel @Inject constructor(
    private val getCycloneUseCase: GetCycloneIntelligenceUseCase,
    private val getEvacuationRoutesUseCase: GetEvacuationRoutesUseCase,
    private val observeMeshNodesUseCase: ObserveMeshNodesUseCase
) : ViewModel() {

    private val userLat = 19.8135
    private val userLon = 85.8312

    val uiState: StateFlow<MapUiState> = combine(
        getCycloneUseCase(),
        getEvacuationRoutesUseCase(userLat, userLon),
        observeMeshNodesUseCase()
    ) { cyclone, routes, nodes ->
        MapUiState(
            cyclone = cyclone,
            routes = routes,
            meshNodes = nodes,
            userLatitude = userLat,
            userLongitude = userLon
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = MapUiState()
    )
}
