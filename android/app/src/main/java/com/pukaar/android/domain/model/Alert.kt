package com.pukaar.android.domain.model

data class Alert(
    val id: String,
    val title: String,
    val description: String,
    val riskLevel: RiskLevel,
    val category: String,
    val zone: String,
    val timestamp: Long,
    val expiresAt: Long,
    val actionAdvice: String,
    val isRead: Boolean = false,
    val isMeshRelayed: Boolean = false
)
