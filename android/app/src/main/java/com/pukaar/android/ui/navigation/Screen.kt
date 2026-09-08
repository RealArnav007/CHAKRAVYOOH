package com.pukaar.android.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CrisisAlert
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Map
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.WifiTethering
import androidx.compose.ui.graphics.vector.ImageVector

sealed class Screen(
    val route: String,
    val title: String,
    val icon: ImageVector? = null,
    val showInBottomNav: Boolean = false
) {
    data object Splash : Screen("splash", "Splash")
    data object Onboarding : Screen("onboarding", "Onboarding")
    data object Home : Screen("home", "Home", Icons.Default.Home, showInBottomNav = true)
    data object Map : Screen("map", "Map", Icons.Default.Map, showInBottomNav = true)
    data object Overview : Screen("overview", "Overview", Icons.Default.Info, showInBottomNav = true)
    data object Alerts : Screen("alerts", "Alerts", Icons.Default.Notifications, showInBottomNav = true)
    data object Sos : Screen("sos", "SOS", Icons.Default.CrisisAlert, showInBottomNav = true)
    data object Mesh : Screen("mesh", "Mesh", Icons.Default.WifiTethering, showInBottomNav = true)
    data object Settings : Screen("settings", "Settings", Icons.Default.Settings, showInBottomNav = false)

    companion object {
        val bottomNavScreens = listOf(Map, Overview, Alerts, Sos, Mesh)
    }
}
