package com.chakravyuh.android.data.api.dto

import com.google.gson.annotations.SerializedName

data class SosPayloadDto(
    @SerializedName("sos_id") val sosId: String,
    @SerializedName("user_id") val userId: String,
    @SerializedName("latitude") val latitude: Double,
    @SerializedName("longitude") val longitude: Double,
    @SerializedName("emergency_type") val emergencyType: String,
    @SerializedName("victim_count") val victimCount: Int,
    @SerializedName("notes") val notes: String,
    @SerializedName("timestamp") val timestamp: Long
)

data class SosResponseDto(
    @SerializedName("status") val status: String,
    @SerializedName("sos_id") val sosId: String,
    @SerializedName("dispatched_at") val dispatchedAt: Long,
    @SerializedName("nearest_responder_eta_minutes") val etaMinutes: Int?
)
