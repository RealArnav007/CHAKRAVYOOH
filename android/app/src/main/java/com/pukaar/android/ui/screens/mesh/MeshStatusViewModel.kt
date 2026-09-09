package com.pukaar.android.ui.screens.mesh

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.domain.model.DeliveryStatus
import com.pukaar.android.domain.model.GatewayStatus
import com.pukaar.android.domain.model.MeshStatus
import com.pukaar.android.domain.model.MeshTransport
import com.pukaar.android.domain.model.PacketLogEntry
import com.pukaar.android.domain.model.PacketLogStatus
import com.pukaar.android.domain.repository.MeshRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class RelayDevice(
    val anonymizedId: String,
    val hopCount: Int,
    val lastSeenMs: Long,
    val transport: MeshTransport
)

data class MeshStatusState(
    val status: MeshStatus = MeshStatus(false, false, 0, GatewayStatus.SEARCHING, DeliveryStatus.PENDING),
    val nearbyDevices: List<RelayDevice> = emptyList(),
    val packetLog: List<PacketLogEntry> = emptyList(),
    val droppedDuplicates: Int = 0,
    val ttlExpired: Int = 0,
    val invalidSig: Int = 0,
    val hasPermissions: Boolean = true
)

@HiltViewModel
class MeshStatusViewModel @Inject constructor(
    private val meshRepository: MeshRepository
) : ViewModel() {

    private val _state = MutableStateFlow(
        MeshStatusState(
            status = MeshStatus(
                internetOnline = true,
                meshActive = true,
                nearbyRelayCount = 4,
                gatewayStatus = GatewayStatus.CONNECTED,
                deliveryStatus = DeliveryStatus.DELIVERED,
                transport = MeshTransport.BOTH
            ),
            nearbyDevices = listOf(
                RelayDevice("ND-7F8A12", 1, System.currentTimeMillis() - 2000, MeshTransport.BLUETOOTH),
                RelayDevice("ND-9C4B83", 1, System.currentTimeMillis() - 4000, MeshTransport.WIFI_AWARE),
                RelayDevice("ND-3E2A99", 2, System.currentTimeMillis() - 12000, MeshTransport.BLUETOOTH),
                RelayDevice("ND-1A0F44", 2, System.currentTimeMillis() - 35000, MeshTransport.WIFI_AWARE)
            )
        )
    )
    val state: StateFlow<MeshStatusState> = _state.asStateFlow()

    init {
        observeMesh()
    }

    private fun observeMesh() {
        viewModelScope.launch {
            combine(
                meshRepository.observeMeshStatus(),
                meshRepository.observePacketLog()
            ) { status, log ->
                val duplicates = log.count { it.status == PacketLogStatus.DROPPED_DUPLICATE }
                val ttl = log.count { it.status == PacketLogStatus.DROPPED_TTL }
                val invalid = log.count { it.status == PacketLogStatus.DROPPED_INVALID_SIG }

                // Keep demo nearby devices if count > 0, otherwise adapt
                val devices = if (status.nearbyRelayCount > 0 && _state.value.nearbyDevices.isEmpty()) {
                    listOf(
                        RelayDevice("ND-7F8A12", 1, System.currentTimeMillis() - 2000, MeshTransport.BLUETOOTH),
                        RelayDevice("ND-9C4B83", 1, System.currentTimeMillis() - 4000, MeshTransport.WIFI_AWARE),
                        RelayDevice("ND-3E2A99", 2, System.currentTimeMillis() - 12000, MeshTransport.BLUETOOTH),
                        RelayDevice("ND-1A0F44", 2, System.currentTimeMillis() - 35000, MeshTransport.WIFI_AWARE)
                    )
                } else _state.value.nearbyDevices

                _state.value.copy(
                    status = if (status.nearbyRelayCount == 0 && status.meshActive) _state.value.status else status,
                    packetLog = log,
                    droppedDuplicates = duplicates,
                    ttlExpired = ttl,
                    invalidSig = invalid,
                    nearbyDevices = devices
                )
            }.collect { updated ->
                _state.value = updated
            }
        }
    }

    fun setPermissionGranted(granted: Boolean) {
        _state.update { it.copy(hasPermissions = granted) }
    }
}
