package com.pukaar.android.ui.screens.alerts

import androidx.compose.runtime.Composable

@Composable
fun AlertsScreen(
    onNavigateToSettings: () -> Unit = {}
) {
    AlertFeedScreen(onNavigateToSettings = onNavigateToSettings)
}
