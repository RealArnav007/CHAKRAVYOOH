package com.pukaar.android.data.api.dto

import com.google.gson.annotations.SerializedName
import com.pukaar.android.domain.model.Alert
import com.pukaar.android.domain.model.RiskLevel

data class AlertDto(
    @SerializedName("id") val id: String,
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String,
    @SerializedName("risk_level") val riskLevel: String,
    @SerializedName("category") val category: String,
    @SerializedName("zone") val zone: String,
    @SerializedName("timestamp") val timestamp: Long,
    @SerializedName("expires_at") val expiresAt: Long,
    @SerializedName("action_advice") val actionAdvice: String
) {
    fun toDomain(): Alert = Alert(
        id = id,
        title = title,
        description = description,
        riskLevel = RiskLevel.fromString(riskLevel),
        category = category,
        zone = zone,
        timestamp = timestamp,
        expiresAt = expiresAt,
        actionAdvice = actionAdvice
    )
}
