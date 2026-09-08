package com.pukaar.android.ui.screens.settings

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
class SettingsViewModel @Inject constructor(
    private val userRepository: UserRepository
) : ViewModel() {

    val profile: StateFlow<UserProfile> = userRepository.getUserProfile()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = UserProfile(
                userId = "node_local",
                name = "Citizen Responder",
                phone = "+91-112",
                bloodGroup = "O+"
            )
        )

    fun updateProfile(newProfile: UserProfile) {
        viewModelScope.launch {
            userRepository.saveProfile(newProfile)
        }
    }

    fun toggleMeshRelay(enabled: Boolean) {
        viewModelScope.launch {
            userRepository.setMeshRelayEnabled(enabled)
        }
    }
}
