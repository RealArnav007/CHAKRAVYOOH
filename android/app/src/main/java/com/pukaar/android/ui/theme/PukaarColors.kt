package com.pukaar.android.ui.theme

import androidx.compose.ui.graphics.Color
import com.pukaar.android.domain.model.RiskLevel

object PukaarColors {
    val BgVoid       = Color(0xFF020811)
    val BgSurface    = Color(0xFF091525)
    val BgElevated   = Color(0xFF0F1E38)
    val AccentCyan   = Color(0xFF00D4FF)
    val AccentRed    = Color(0xFFFF1744)
    val AccentAmber  = Color(0xFFFF9100)
    val AccentGreen  = Color(0xFF00E676)
    val AccentYellow = Color(0xFFFFD600)
    val TextPrimary  = Color(0xFFE8F4FF)
    val TextSecondary = Color(0xFF5E7FA4)

    // Risk level colors
    fun forRiskLevel(level: RiskLevel): Color = when (level) {
        RiskLevel.EXTREME  -> AccentRed
        RiskLevel.HIGH     -> Color(0xFFFF6D00)
        RiskLevel.MODERATE -> AccentYellow
        RiskLevel.LOW      -> AccentGreen
    }
}
