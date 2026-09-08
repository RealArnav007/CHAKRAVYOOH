package com.pukaar.android.data.api.dto

import com.google.gson.annotations.SerializedName

data class CycloneAlertDto(
    @SerializedName("alert_id") val alertId: String,
    @SerializedName("version") val version: Int,
    @SerializedName("issued_at") val issuedAt: String,
    @SerializedName("updated_at") val updatedAt: String,
    @SerializedName("valid_until") val validUntil: String,
    @SerializedName("supersedes") val supersedes: String?,
    @SerializedName("risk_level") val riskLevel: String,
    @SerializedName("message") val message: String,
    @SerializedName("affected_zones") val affectedZones: List<String>?,
    @SerializedName("signature") val signature: String
)
