package com.pukaar.android.data.api.dto

import com.google.gson.annotations.SerializedName

data class SosDispatchDto(
    @SerializedName("sos_id") val sosId: String,
    @SerializedName("sender_id") val senderId: String,
    @SerializedName("sender_name") val senderName: String,
    @SerializedName("latitude") val latitude: Double,
    @SerializedName("longitude") val longitude: Double,
    @SerializedName("emergency_type") val emergencyType: String,
    @SerializedName("victim_count") val victimCount: Int,
    @SerializedName("notes") val notes: String,
    @SerializedName("signature") val signature: String,
    @SerializedName("timestamp") val timestamp: Long
)

data class SosStatusResponseDto(
    @SerializedName("sos_id") val sosId: String,
    @SerializedName("status") val status: String,
    @SerializedName("dispatched_team") val dispatchedTeam: String?,
    @SerializedName("eta_minutes") val etaMinutes: Int?
)
