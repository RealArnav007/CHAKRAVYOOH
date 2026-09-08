package com.pukaar.android.data.api.dto

import com.google.gson.annotations.SerializedName

data class RiskZoneDto(
    @SerializedName("zone_id") val zoneId: String,
    @SerializedName("zone_name") val zoneName: String,
    @SerializedName("risk_level") val riskLevel: String,
    @SerializedName("polygon") val polygon: List<LatLngDto>?
)
