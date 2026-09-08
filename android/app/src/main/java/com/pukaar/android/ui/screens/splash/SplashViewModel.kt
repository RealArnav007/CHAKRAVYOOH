package com.pukaar.android.ui.screens.splash

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.domain.repository.UserRepository
import com.pukaar.android.domain.usecase.GetAlertsUseCase
import com.pukaar.android.domain.usecase.GetCycloneDataUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

@HiltViewModel
class SplashViewModel @Inject constructor(
    private val getCycloneDataUseCase: GetCycloneDataUseCase,
    private val getAlertsUseCase: GetAlertsUseCase,
    private val userRepository: UserRepository
) : ViewModel() {

    private val _isReady = MutableStateFlow(false)
    val isReady = _isReady.asStateFlow()

    private val _isOnboardingComplete = MutableStateFlow(false)
    val isOnboardingComplete = _isOnboardingComplete.asStateFlow()

    init {
        viewModelScope.launch {
            launch { getCycloneDataUseCase.refresh() }
            launch { getAlertsUseCase.refresh() }
            val profile = userRepository.getUserProfile().first()
            _isOnboardingComplete.value = profile.isOnboardingComplete
            delay(1200)
            _isReady.value = true
        }
    }
}
