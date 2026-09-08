package com.chakravyuh.android.ui.screens.mesh

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chakravyuh.android.domain.model.MeshMessage
import com.chakravyuh.android.domain.model.MeshNode
import com.chakravyuh.android.domain.repository.MeshRepository
import com.chakravyuh.android.domain.usecase.ObserveMeshNodesUseCase
import com.chakravyuh.android.domain.usecase.SendMeshMessageUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class MeshUiState(
    val discoveredNodes: List<MeshNode> = emptyList(),
    val messages: List<MeshMessage> = emptyList(),
    val isRelayActive: Boolean = true
)

@HiltViewModel
class MeshViewModel @Inject constructor(
    private val observeMeshNodesUseCase: ObserveMeshNodesUseCase,
    private val sendMeshMessageUseCase: SendMeshMessageUseCase,
    private val meshRepository: MeshRepository
) : ViewModel() {

    val uiState: StateFlow<MeshUiState> = combine(
        observeMeshNodesUseCase(),
        meshRepository.getMeshMessagesStream()
    ) { nodes, messages ->
        MeshUiState(
            discoveredNodes = nodes,
            messages = messages,
            isRelayActive = true
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = MeshUiState()
    )

    fun sendBroadcast(text: String) {
        viewModelScope.launch {
            sendMeshMessageUseCase.broadcast(text)
        }
    }

    fun toggleRelay(enable: Boolean) {
        viewModelScope.launch {
            if (enable) observeMeshNodesUseCase.startMeshRelay()
            else observeMeshNodesUseCase.stopMeshRelay()
        }
    }
}
