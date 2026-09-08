package com.chakravyuh.android.ui.screens.sos

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chakravyuh.android.domain.model.SosRequest
import com.chakravyuh.android.domain.repository.SosRepository
import com.chakravyuh.android.domain.usecase.SendSosUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class SosUiState(
    val activeSos: SosRequest? = null,
    val selectedEmergencyType: String = "MEDICAL",
    val victimCount: Int = 1,
    val notes: String = "",
    val isTriggering: Boolean = false
)

@HiltViewModel
class SosViewModel @Inject constructor(
    private val sendSosUseCase: SendSosUseCase,
    private val sosRepository: SosRepository
) : ViewModel() {

    val activeSos: StateFlow<SosRequest?> = sosRepository.getActiveSosStream()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = null
        )

    fun triggerEmergencySos(
        lat: Double = 19.8135,
        lon: Double = 85.8312,
        emergencyType: String,
        victimCount: Int,
        notes: String
    ) {
        viewModelScope.launch {
            sendSosUseCase(lat, lon, emergencyType, victimCount, notes)
        }
    }

    fun cancelEmergency(sosId: String) {
        viewModelScope.launch {
            sendSosUseCase.cancel(sosId)
        }
    }
}
