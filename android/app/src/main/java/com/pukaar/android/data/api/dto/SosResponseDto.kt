package com.pukaar.android.data.api.dto

import com.google.gson.annotations.SerializedName

data class SosResponseDto(
    @SerializedName("sos_id") val sosId: String,
    @SerializedName("status") val status: String,
    @SerializedName("received_at") val receivedAt: Long
)
