package com.pukaar.android.ui.theme

import android.app.Activity
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val PukaarDarkColorScheme = darkColorScheme(
    primary = PukaarColors.AccentCyan,
    onPrimary = PukaarColors.BgVoid,
    primaryContainer = PukaarColors.BgElevated,
    onPrimaryContainer = PukaarColors.TextPrimary,
    background = PukaarColors.BgVoid,
    onBackground = PukaarColors.TextPrimary,
    surface = PukaarColors.BgSurface,
    onSurface = PukaarColors.TextPrimary,
    surfaceVariant = PukaarColors.BgElevated,
    onSurfaceVariant = PukaarColors.TextSecondary,
    error = PukaarColors.AccentRed,
    onError = Color.White,
    outline = PukaarColors.BgElevated
)

@Composable
fun PukaarTheme(
    content: @Composable () -> Unit
) {
    val view = LocalView.current

    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = Color.Transparent.toArgb()
            window.navigationBarColor = Color.Transparent.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = false
            WindowCompat.getInsetsController(window, view).isAppearanceLightNavigationBars = false
        }
    }

    MaterialTheme(
        colorScheme = PukaarDarkColorScheme,
        typography = PukaarTypography,
        content = content
    )
}
