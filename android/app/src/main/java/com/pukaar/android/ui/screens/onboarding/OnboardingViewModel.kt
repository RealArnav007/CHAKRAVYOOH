package com.pukaar.android.ui.screens.onboarding

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.domain.model.UserProfile
import com.pukaar.android.domain.repository.UserRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

@HiltViewModel
class OnboardingViewModel @Inject constructor(
    private val userRepository: UserRepository
) : ViewModel() {

    val profile: StateFlow<UserProfile> = userRepository.getUserProfile()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = UserProfile(
                userId = "node_pukaar_01",
                name = "",
                phone = "",
                bloodGroup = "O+"
            )
        )

    fun completeOnboarding(name: String, phone: String, bloodGroup: String, meshRelay: Boolean) {
        viewModelScope.launch {
            val updated = profile.value.copy(
                name = name,
                phone = phone,
                bloodGroup = bloodGroup,
                isMeshRelayEnabled = meshRelay,
                isOnboardingComplete = true
            )
            userRepository.saveProfile(updated)
            userRepository.setOnboardingComplete(true)
        }
    }
}
