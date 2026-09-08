package com.chakravyuh.android.ui.screens.splash

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chakravyuh.android.domain.usecase.GetAlertsUseCase
import com.chakravyuh.android.domain.usecase.GetCycloneIntelligenceUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

@HiltViewModel
class SplashViewModel @Inject constructor(
    private val getCycloneIntelligenceUseCase: GetCycloneIntelligenceUseCase,
    private val getAlertsUseCase: GetAlertsUseCase
) : ViewModel() {

    private val _isReady = MutableStateFlow(false)
    val isReady = _isReady.asStateFlow()

    init {
        viewModelScope.launch {
            // Warm up initial cache & offline seeds
            launch { getCycloneIntelligenceUseCase.refresh() }
            launch { getAlertsUseCase.refresh() }
            delay(1500) // Tactical splash transition delay
            _isReady.value = true
        }
    }
}
