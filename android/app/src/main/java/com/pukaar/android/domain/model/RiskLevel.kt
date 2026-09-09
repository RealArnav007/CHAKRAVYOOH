package com.pukaar.android.domain.model

enum class RiskLevel {
    EXTREME,
    HIGH,
    MODERATE,
    LOW;

    companion object {
        fun fromString(value: String?): RiskLevel {
            return when (value?.uppercase()) {
                "EXTREME", "RED", "CRITICAL" -> EXTREME
                "HIGH", "ORANGE", "SEVERE" -> HIGH
                "MODERATE", "YELLOW", "CAUTION" -> MODERATE
                "LOW", "GREEN", "SAFE" -> LOW
                else -> LOW
            }
        }
    }
}
