package com.pukaar.android.ui.screens.onboarding

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.data.api.PukaarApi
import com.pukaar.android.data.api.dto.KeyRegistrationDto
import com.pukaar.android.data.crypto.DeviceKeyManager
import com.pukaar.android.domain.repository.UserRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

enum class SetupStepState {
    PENDING,
    IN_PROGRESS,
    SUCCESS,
    FAILED
}

data class OnboardingSetupState(
    val keyGenState: SetupStepState = SetupStepState.PENDING,
    val serverRegState: SetupStepState = SetupStepState.PENDING,
    val locationGranted: Boolean = false,
    val bluetoothGranted: Boolean = false,
    val wifiGranted: Boolean = false,
    val canProceed: Boolean = false
)

@HiltViewModel
class OnboardingViewModel @Inject constructor(
    private val deviceKeyManager: DeviceKeyManager,
    private val pukaarApi: PukaarApi,
    private val userRepository: UserRepository
) : ViewModel() {

    private val _setupState = MutableStateFlow(OnboardingSetupState())
    val setupState: StateFlow<OnboardingSetupState> = _setupState.asStateFlow()

    fun startSetup() {
        if (_setupState.value.keyGenState != SetupStepState.PENDING) return

        viewModelScope.launch {
            // 1. Generate Keystore Identity
            _setupState.update { it.copy(keyGenState = SetupStepState.IN_PROGRESS) }
            delay(800)

            deviceKeyManager.generateKeyPairIfAbsent()
            val publicKey = deviceKeyManager.getPublicKeyBase64()

            _setupState.update { it.copy(keyGenState = SetupStepState.SUCCESS, serverRegState = SetupStepState.IN_PROGRESS, canProceed = true) }

            // 2. Register key with backend API
            delay(600)
            try {
                val deviceId = "NODE-" + UUID.randomUUID().toString().take(8).uppercase()
                pukaarApi.registerKey(KeyRegistrationDto(deviceId = deviceId, publicKey = publicKey))
                _setupState.update { it.copy(serverRegState = SetupStepState.SUCCESS) }
            } catch (e: Exception) {
                _setupState.update { it.copy(serverRegState = SetupStepState.FAILED) }
            }
        }
    }

    fun setLocationGranted(granted: Boolean) {
        _setupState.update { it.copy(locationGranted = granted) }
    }

    fun setBluetoothGranted(granted: Boolean) {
        _setupState.update { it.copy(bluetoothGranted = granted) }
    }

    fun setWifiGranted(granted: Boolean) {
        _setupState.update { it.copy(wifiGranted = granted) }
    }

    fun completeOnboarding(onSuccess: () -> Unit) {
        viewModelScope.launch {
            userRepository.setOnboardingComplete(true)
            onSuccess()
        }
    }
}
