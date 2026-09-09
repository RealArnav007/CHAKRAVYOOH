package com.pukaar.android.ui.screens.sos.inbox

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.domain.model.IncomingSos
import com.pukaar.android.domain.model.MeshPacket
import com.pukaar.android.domain.model.MeshPriority
import com.pukaar.android.domain.model.MessageType
import com.pukaar.android.domain.model.RelayStatus
import com.pukaar.android.domain.repository.MeshRepository
import com.pukaar.android.domain.repository.SosRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.time.Instant
import javax.inject.Inject

data class SosInboxState(
    val incoming: List<IncomingSos> = emptyList(),
    val isLoading: Boolean = false
)

@HiltViewModel
class SosInboxViewModel @Inject constructor(
    private val sosRepository: SosRepository,
    private val meshRepository: MeshRepository
) : ViewModel() {

    private val _state = MutableStateFlow(SosInboxState(isLoading = true))
    val state: StateFlow<SosInboxState> = _state.asStateFlow()

    init {
        observeInbox()
    }

    private fun observeInbox() {
        viewModelScope.launch {
            sosRepository.observeIncomingSos().collect { list ->
                _state.update {
                    it.copy(
                        incoming = list.sortedByDescending { item -> item.receivedAt },
                        isLoading = false
                    )
                }
            }
        }
    }

    fun relayManually(msgId: String) {
        viewModelScope.launch {
            val sos = _state.value.incoming.find { it.msgId == msgId } ?: return@launch

            val rawPayload = "{\"emergency_type\":\"${sos.emergencyType.name}\",\"latitude\":${sos.latitude},\"longitude\":${sos.longitude},\"message\":\"${sos.message ?: ""}\"}"
            val packet = MeshPacket(
                msgId = sos.msgId,
                messageType = MessageType.SOS,
                createdAt = Instant.ofEpochMilli(sos.receivedAt).toString(),
                ttl = 6,
                hops = sos.hopCount + 1,
                priority = MeshPriority.P0,
                senderIdentity = sos.senderHash,
                signature = "RELAY_SIG_" + sos.senderHash,
                encryptedPayload = rawPayload
            )

            val result = meshRepository.relayPacket(packet)
            if (result.isSuccess) {
                sosRepository.updateRelayStatus(msgId, RelayStatus.RELAYED)
            } else {
                sosRepository.updateRelayStatus(msgId, RelayStatus.RELAY_FAILED)
            }
        }
    }
}
