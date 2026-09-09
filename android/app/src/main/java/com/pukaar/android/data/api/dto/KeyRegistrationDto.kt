package com.pukaar.android.data.api.dto

import com.google.gson.annotations.SerializedName

data class KeyRegistrationDto(
    @SerializedName("node_id") val nodeId: String,
    @SerializedName("public_key_hex") val publicKeyHex: String,
    @SerializedName("alias") val alias: String,
    @SerializedName("timestamp") val timestamp: Long
)
