package com.pukaar.android.domain.model

data class MeshStatus(
    val internetOnline: Boolean,
    val meshActive: Boolean,
    val nearbyRelayCount: Int,
    val gatewayStatus: GatewayStatus,
    val deliveryStatus: DeliveryStatus,
    val transport: MeshTransport = MeshTransport.NONE
)

enum class GatewayStatus {
    CONNECTED,
    SEARCHING,
    UNAVAILABLE
}

enum class DeliveryStatus {
    DELIVERED,
    PENDING,
    FAILED,
    NOT_SENT
}

enum class MeshTransport {
    NONE,
    BLUETOOTH,
    WIFI_AWARE,
    BOTH
}
