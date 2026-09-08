package com.pukaar.android.ui.screens.overview

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.domain.model.CycloneData
import com.pukaar.android.domain.usecase.GetCycloneDataUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn

@HiltViewModel
class OverviewViewModel @Inject constructor(
    private val getCycloneUseCase: GetCycloneDataUseCase
) : ViewModel() {

    val cyclone: StateFlow<CycloneData?> = getCycloneUseCase()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = null
        )
}
