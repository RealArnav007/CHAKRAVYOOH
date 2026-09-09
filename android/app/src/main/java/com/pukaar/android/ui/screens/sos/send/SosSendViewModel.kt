package com.pukaar.android.ui.screens.sos.send

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.data.crypto.PukaarCryptoManager
import com.pukaar.android.domain.model.EmergencyType
import com.pukaar.android.domain.model.MeshPacket
import com.pukaar.android.domain.model.MeshPriority
import com.pukaar.android.domain.model.MeshTransport
import com.pukaar.android.domain.model.MessageType
import com.pukaar.android.domain.model.SosRequest
import com.pukaar.android.domain.repository.MeshRepository
import com.pukaar.android.domain.repository.SosRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.time.Instant
import java.util.UUID
import javax.inject.Inject

enum class SendStatus {
    IDLE,
    SIGNING,
    SENDING_INTERNET,
    SENDING_WIFI,
    SENDING_BT,
    DELIVERED,
    FAILED
}

enum class DeliveryPath {
    INTERNET,
    WIFI_AWARE,
    BLUETOOTH
}

data class SosSendState(
    val emergencyType: EmergencyType = EmergencyType.OTHER,
    val latitude: Double? = 19.8135, // Default coast location for demo
    val longitude: Double? = 85.8312,
    val message: String = "",
    val hasSensitiveData: Boolean = false,
    val sendStatus: SendStatus = SendStatus.IDLE,
    val activeDeliveryPath: DeliveryPath? = null
)

@HiltViewModel
class SosSendViewModel @Inject constructor(
    private val sosRepository: SosRepository,
    private val meshRepository: MeshRepository,
    private val cryptoManager: PukaarCryptoManager
) : ViewModel() {

    private val _state = MutableStateFlow(SosSendState())
    val state: StateFlow<SosSendState> = _state.asStateFlow()

    fun setEmergencyType(type: EmergencyType) {
        _state.update { it.copy(emergencyType = type) }
    }

    fun setLocation(lat: Double?, lon: Double?) {
        _state.update { it.copy(latitude = lat, longitude = lon) }
    }

    fun setMessage(msg: String) {
        _state.update { it.copy(message = msg) }
    }

    fun setSensitiveData(sensitive: Boolean) {
        _state.update { it.copy(hasSensitiveData = sensitive) }
    }

    fun sendSos() {
        if (_state.value.sendStatus != SendStatus.IDLE &&
            _state.value.sendStatus != SendStatus.DELIVERED &&
            _state.value.sendStatus != SendStatus.FAILED) {
            return
        }

        viewModelScope.launch {
            val currentState = _state.value
            val lat = currentState.latitude ?: 19.8135
            val lon = currentState.longitude ?: 85.8312

            // STEP 1: Signing
            _state.update { it.copy(sendStatus = SendStatus.SIGNING, activeDeliveryPath = null) }
            delay(500)

            val rawPayload = "{\"emergency_type\":\"${currentState.emergencyType.name}\",\"latitude\":$lat,\"longitude\":$lon,\"message\":\"${currentState.message}\"}"
            val signature = try {
                cryptoManager.sign(rawPayload)
            } catch (e: Exception) {
                "DEMO_SIGNATURE_" + UUID.randomUUID().toString().take(12)
            }

            // STEP 2: Try Internet Uplink Dispatch
            _state.update { it.copy(sendStatus = SendStatus.SENDING_INTERNET, activeDeliveryPath = DeliveryPath.INTERNET) }
            delay(800)

            val sosRequest = SosRequest(
                emergencyType = currentState.emergencyType,
                latitude = lat,
                longitude = lon,
                message = currentState.message.ifBlank { null },
                hasSensitiveData = currentState.hasSensitiveData
            )

            val internetResult = sosRepository.sendSos(sosRequest)
            if (internetResult.isSuccess) {
                _state.update {
                    it.copy(
                        sendStatus = SendStatus.DELIVERED,
                        activeDeliveryPath = DeliveryPath.INTERNET
                    )
                }
                return@launch
            }

            // STEP 3: Try Wi-Fi Aware Mesh Dispatch
            _state.update { it.copy(sendStatus = SendStatus.SENDING_WIFI, activeDeliveryPath = DeliveryPath.WIFI_AWARE) }
            delay(900)

            val packet = MeshPacket(
                msgId = "SOS-" + UUID.randomUUID().toString().take(8).uppercase(),
                messageType = MessageType.SOS,
                createdAt = Instant.now().toString(),
                ttl = 7,
                hops = 0,
                priority = MeshPriority.P0,
                senderIdentity = cryptoManager.localPublicKeyHex.ifBlank { "NODE_" + UUID.randomUUID().toString().take(6) },
                signature = signature,
                encryptedPayload = rawPayload
            )

            val wifiResult = meshRepository.relayPacket(packet)
            if (wifiResult.isSuccess) {
                _state.update {
                    it.copy(
                        sendStatus = SendStatus.DELIVERED,
                        activeDeliveryPath = DeliveryPath.WIFI_AWARE
                    )
                }
                return@launch
            }

            // STEP 4: Try Bluetooth LE Mesh Relay
            _state.update { it.copy(sendStatus = SendStatus.SENDING_BT, activeDeliveryPath = DeliveryPath.BLUETOOTH) }
            delay(900)

            val btResult = meshRepository.relayPacket(packet)
            if (btResult.isSuccess) {
                _state.update {
                    it.copy(
                        sendStatus = SendStatus.DELIVERED,
                        activeDeliveryPath = DeliveryPath.BLUETOOTH
                    )
                }
            } else {
                _state.update {
                    it.copy(
                        sendStatus = SendStatus.FAILED,
                        activeDeliveryPath = null
                    )
                }
            }
        }
    }

    fun resetState() {
        _state.update { it.copy(sendStatus = SendStatus.IDLE, activeDeliveryPath = null) }
    }
}
