package com.pukaar.android.data.mesh

import com.pukaar.android.domain.model.DeliveryStatus
import com.pukaar.android.domain.model.GatewayStatus
import com.pukaar.android.domain.model.MeshStatus
import com.pukaar.android.domain.model.MeshTransport
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class MeshStatusObserver @Inject constructor() {
    private val _statusFlow = MutableStateFlow(
        MeshStatus(
            internetOnline = false,
            meshActive = false,
            nearbyRelayCount = 0,
            gatewayStatus = GatewayStatus.SEARCHING,
            deliveryStatus = DeliveryStatus.PENDING,
            transport = MeshTransport.NONE
        )
    )
    val statusFlow: StateFlow<MeshStatus> = _statusFlow.asStateFlow()

    fun updateStatus(status: MeshStatus) {
        _statusFlow.value = status
    }
}
