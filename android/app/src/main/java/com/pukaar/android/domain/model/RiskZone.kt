package com.pukaar.android.domain.model

data class RiskZone(
    val zoneId: String,
    val zoneName: String,
    val riskLevel: RiskLevel,
    val polygon: List<LatLng>
)
