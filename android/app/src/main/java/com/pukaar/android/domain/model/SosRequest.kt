package com.pukaar.android.domain.model

data class SosRequest(
    val emergencyType: EmergencyType,
    val latitude: Double,
    val longitude: Double,
    val message: String?,
    val hasSensitiveData: Boolean
)
