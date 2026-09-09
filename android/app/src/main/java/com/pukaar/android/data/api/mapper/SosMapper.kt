package com.pukaar.android.data.api.mapper

import com.pukaar.android.data.api.dto.SosRequestDto
import com.pukaar.android.domain.model.EmergencyType
import com.pukaar.android.domain.model.SosRequest

fun SosRequest.toDto(): SosRequestDto {
    return SosRequestDto(
        emergencyType = emergencyType.name,
        latitude = latitude,
        longitude = longitude,
        message = message,
        hasSensitiveData = hasSensitiveData
    )
}

fun SosRequestDto.toDomain(): SosRequest {
    val type = try {
        EmergencyType.valueOf(emergencyType)
    } catch (e: Exception) {
        EmergencyType.OTHER
    }

    return SosRequest(
        emergencyType = type,
        latitude = latitude,
        longitude = longitude,
        message = message,
        hasSensitiveData = hasSensitiveData
    )
}
