package com.chakravyuh.android.domain.model

/**
 * Domain representation of an emergency/hazard alert emitted by the risk engine.
 */
data class Alert(
    val id: String,
    val title: String,
    val description: String,
    val threatLevel: ThreatLevel,
    val category: String, // e.g. "CYCLONE", "STORM_SURGE", "WIND_GUST", "FLOOD"
    val zoneId: String,
    val affectedAreaName: String,
    val timestamp: Long,
    val expiresAt: Long,
    val actionAdvice: String,
    val isRead: Boolean = false,
    val isBroadcastingViaMesh: Boolean = false
)
