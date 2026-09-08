package com.pukaar.android.data.api.dto

import com.google.gson.annotations.SerializedName

data class SosRequestDto(
    @SerializedName("emergency_type") val emergencyType: String,
    @SerializedName("latitude") val latitude: Double,
    @SerializedName("longitude") val longitude: Double,
    @SerializedName("message") val message: String?,
    @SerializedName("has_sensitive_data") val hasSensitiveData: Boolean
)
