package com.pukaar.android.ui.screens.mesh

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.pukaar.android.domain.model.MeshPeer
import com.pukaar.android.domain.model.SosMessage
import com.pukaar.android.domain.repository.SosRepository
import com.pukaar.android.domain.usecase.ObserveMeshPeersUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class MeshState(
    val peers: List<MeshPeer> = emptyList(),
    val packets: List<SosMessage> = emptyList(),
    val isRelayActive: Boolean = true
)

@HiltViewModel
class MeshViewModel @Inject constructor(
    private val observeMeshPeersUseCase: ObserveMeshPeersUseCase,
    private val sosRepository: SosRepository
) : ViewModel() {

    val state: StateFlow<MeshState> = combine(
        observeMeshPeersUseCase(),
        sosRepository.getSosInboxStream()
    ) { peers, packets ->
        MeshState(peers = peers, packets = packets)
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = MeshState()
    )

    fun toggleRelay(enabled: Boolean) {
        viewModelScope.launch {
            if (enabled) observeMeshPeersUseCase.startRelay()
            else observeMeshPeersUseCase.stopRelay()
        }
    }
}
