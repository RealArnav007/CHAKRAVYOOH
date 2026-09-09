package com.pukaar.android.ui.screens.overview

import androidx.compose.runtime.Composable

@Composable
fun OverviewScreen(
    onNavigateToSettings: () -> Unit = {}
) {
    CycloneOverviewScreen(onNavigateToSettings = onNavigateToSettings)
}
