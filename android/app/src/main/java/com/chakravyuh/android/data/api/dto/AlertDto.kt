package com.chakravyuh.android.data.api.dto

import com.chakravyuh.android.domain.model.Alert
import com.chakravyuh.android.domain.model.ThreatLevel
import com.google.gson.annotations.SerializedName

data class AlertDto(
    @SerializedName("id") val id: String,
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String,
    @SerializedName("threat_level") val threatLevel: String,
    @SerializedName("category") val category: String,
    @SerializedName("zone_id") val zoneId: String,
    @SerializedName("affected_area") val affectedArea: String,
    @SerializedName("timestamp") val timestamp: Long,
    @SerializedName("expires_at") val expiresAt: Long,
    @SerializedName("action_advice") val actionAdvice: String
) {
    fun toDomain(): Alert {
        return Alert(
            id = id,
            title = title,
            description = description,
            threatLevel = ThreatLevel.fromString(threatLevel),
            category = category,
            zoneId = zoneId,
            affectedAreaName = affectedArea,
            timestamp = timestamp,
            expiresAt = expiresAt,
            actionAdvice = actionAdvice
        )
    }
}
