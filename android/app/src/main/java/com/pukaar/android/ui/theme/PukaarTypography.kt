package com.pukaar.android.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.googlefonts.Font
import androidx.compose.ui.text.googlefonts.GoogleFont
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp

val GoogleFontProvider = GoogleFont.Provider(
    providerAuthority = "com.google.android.gms.fonts",
    providerPackage = "com.google.android.gms",
    certificates = 0 // In XML or system certificate bundle
)

val RajdhaniFont = GoogleFont("Rajdhani")
val JetBrainsMonoFont = GoogleFont("JetBrains Mono")

val RajdhaniFontFamily = FontFamily(
    Font(googleFont = RajdhaniFont, fontProvider = GoogleFontProvider, weight = FontWeight.Bold, style = FontStyle.Normal)
)

val JetBrainsMonoFamily = FontFamily(
    Font(googleFont = JetBrainsMonoFont, fontProvider = GoogleFontProvider, weight = FontWeight.Normal, style = FontStyle.Normal)
)

val PukaarTypography = Typography(
    displayLarge = TextStyle(
        fontFamily = RajdhaniFontFamily,
        fontSize = 48.sp,
        letterSpacing = 0.05.em
    ),
    headlineLarge = TextStyle(
        fontFamily = RajdhaniFontFamily,
        fontSize = 32.sp,
        letterSpacing = 0.08.em
    ),
    headlineMedium = TextStyle(
        fontFamily = RajdhaniFontFamily,
        fontSize = 24.sp,
        letterSpacing = 0.08.em
    ),
    titleLarge = TextStyle(
        fontFamily = RajdhaniFontFamily,
        fontSize = 20.sp,
        letterSpacing = 0.05.em
    ),
    labelLarge = TextStyle(
        fontFamily = JetBrainsMonoFamily,
        fontSize = 14.sp
    ),
    labelMedium = TextStyle(
        fontFamily = JetBrainsMonoFamily,
        fontSize = 12.sp
    ),
    bodyMedium = TextStyle(
        fontSize = 14.sp,
        color = PukaarColors.TextPrimary
    ),
    bodySmall = TextStyle(
        fontSize = 12.sp,
        color = PukaarColors.TextSecondary
    )
)
