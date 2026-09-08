package com.chakravyuh.android.domain.model

import androidx.compose.ui.graphics.Color
import com.chakravyuh.android.ui.theme.ThreatExtreme
import com.chakravyuh.android.ui.theme.ThreatHigh
import com.chakravyuh.android.ui.theme.ThreatLow
import com.chakravyuh.android.ui.theme.ThreatModerate
import com.chakravyuh.android.ui.theme.ChakravyuhPrimary

/**
 * Chakravyuh threat level severity representation.
 */
enum class ThreatLevel(val label: String, val color: Color) {
    EXTREME("EXTREME", ThreatExtreme),
    HIGH("HIGH", ThreatHigh),
    MODERATE("MODERATE", ThreatModerate),
    LOW("LOW", ThreatLow),
    NORMAL("NORMAL", ChakravyuhPrimary);

    companion object {
        fun fromString(value: String?): ThreatLevel {
            return when (value?.uppercase()) {
                "EXTREME", "RED", "CRITICAL" -> EXTREME
                "HIGH", "ORANGE", "SEVERE" -> HIGH
                "MODERATE", "YELLOW", "CAUTION" -> MODERATE
                "LOW", "GREEN", "SAFE" -> LOW
                else -> NORMAL
            }
        }
    }
}
