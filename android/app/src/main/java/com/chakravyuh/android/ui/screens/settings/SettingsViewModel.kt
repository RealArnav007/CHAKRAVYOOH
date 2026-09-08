package com.chakravyuh.android.ui.screens.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chakravyuh.android.domain.model.UserSettings
import com.chakravyuh.android.domain.repository.SettingsRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val settingsRepository: SettingsRepository
) : ViewModel() {

    val settings: StateFlow<UserSettings> = settingsRepository.getUserSettings()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = UserSettings(
                userId = "node_local",
                userName = "Citizen Responder",
                emergencyContactPhone = "+91-112",
                bloodGroup = "O+"
            )
        )

    fun updateSettings(newSettings: UserSettings) {
        viewModelScope.launch {
            settingsRepository.updateSettings(newSettings)
        }
    }

    fun toggleMeshRelay(enabled: Boolean) {
        viewModelScope.launch {
            settingsRepository.setMeshRelayEnabled(enabled)
        }
    }
}
