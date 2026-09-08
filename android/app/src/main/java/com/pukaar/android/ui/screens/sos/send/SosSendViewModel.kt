package com.pukaar.android.ui.screens.sos.send

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.domain.model.SosMessage
import com.pukaar.android.domain.usecase.SendSosUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

@HiltViewModel
class SosSendViewModel @Inject constructor(
    private val sendSosUseCase: SendSosUseCase
) : ViewModel() {

    val activeSos: StateFlow<SosMessage?> = sendSosUseCase.getActiveOutgoingSos()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = null
        )

    fun sendEmergencySos(
        latitude: Double = 19.8135,
        longitude: Double = 85.8312,
        emergencyType: String,
        victimCount: Int,
        notes: String
    ) {
        viewModelScope.launch {
            sendSosUseCase(latitude, longitude, emergencyType, victimCount, notes)
        }
    }

    fun cancelSos(sosId: String) {
        viewModelScope.launch {
            sendSosUseCase.cancel(sosId)
        }
    }
}
