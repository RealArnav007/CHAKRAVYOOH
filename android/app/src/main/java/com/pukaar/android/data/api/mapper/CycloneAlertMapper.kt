package com.pukaar.android.data.api.mapper

import com.pukaar.android.data.api.dto.CycloneAlertDto
import com.pukaar.android.domain.model.CycloneAlert
import com.pukaar.android.domain.model.RiskLevel
import com.pukaar.android.domain.model.VerificationStatus

fun CycloneAlertDto.toDomain(): CycloneAlert {
    val level = try {
        RiskLevel.valueOf(riskLevel.uppercase())
    } catch (e: Exception) {
        RiskLevel.MODERATE
    }

    return CycloneAlert(
        alertId = alertId,
        version = version,
        issuedAt = issuedAt,
        updatedAt = updatedAt,
        validUntil = validUntil,
        supersedes = supersedes,
        riskLevel = level,
        message = message,
        affectedZones = affectedZones ?: emptyList(),
        signature = signature,
        verificationStatus = VerificationStatus.PENDING
    )
}
