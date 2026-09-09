package com.pukaar.android.ui.screens.mesh

import androidx.compose.runtime.Composable

@Composable
fun MeshScreen(
    onNavigateToSettings: () -> Unit = {}
) {
    MeshStatusScreen(onNavigateToSettings = onNavigateToSettings)
}
