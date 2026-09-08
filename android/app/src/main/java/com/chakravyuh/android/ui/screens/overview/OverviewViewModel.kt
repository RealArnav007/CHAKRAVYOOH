package com.chakravyuh.android.ui.screens.overview

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chakravyuh.android.domain.model.CycloneIntelligence
import com.chakravyuh.android.domain.usecase.GetCycloneIntelligenceUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn

data class OverviewUiState(
    val cyclone: CycloneIntelligence? = null,
    val isLoading: Boolean = false
)

@HiltViewModel
class OverviewViewModel @Inject constructor(
    private val getCycloneUseCase: GetCycloneIntelligenceUseCase
) : ViewModel() {

    val uiState: StateFlow<OverviewUiState> = getCycloneUseCase()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = null
        ).let { flow ->
            kotlinx.coroutines.flow.map(flow) { cyclone ->
                OverviewUiState(cyclone = cyclone, isLoading = cyclone == null)
            }.stateIn(
                scope = viewModelScope,
                started = SharingStarted.WhileSubscribed(5000),
                initialValue = OverviewUiState(isLoading = true)
            )
        }
}
