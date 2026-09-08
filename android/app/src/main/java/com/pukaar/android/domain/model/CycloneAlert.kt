package com.pukaar.android.domain.model

data class CycloneAlert(
    val alertId: String,
    val version: Int,
    val issuedAt: String,
    val updatedAt: String,
    val validUntil: String,
    val supersedes: String?,
    val riskLevel: RiskLevel,
    val message: String,
    val affectedZones: List<String>,
    val signature: String,
    val verificationStatus: VerificationStatus
)

enum class VerificationStatus {
    VERIFIED,
    UNVERIFIED,
    INVALID,
    PENDING
}
