package com.chakravyuh.android.data.websocket

import com.chakravyuh.android.domain.model.Alert
import com.chakravyuh.android.domain.model.CycloneIntelligence
import com.chakravyuh.android.domain.model.MeshMessage

sealed class WebSocketEvent {
    data class CycloneUpdate(val intelligence: CycloneIntelligence) : WebSocketEvent()
    data class NewAlert(val alert: Alert) : WebSocketEvent()
    data class MeshRelayPacket(val packet: MeshMessage) : WebSocketEvent()
    data class SosBroadcast(val sosId: String, val lat: Double, val lon: Double) : WebSocketEvent()
    data object Connected : WebSocketEvent()
    data object Disconnected : WebSocketEvent()
    data class Error(val throwable: Throwable) : WebSocketEvent()
}
