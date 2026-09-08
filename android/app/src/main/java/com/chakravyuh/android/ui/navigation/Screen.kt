package com.chakravyuh.android.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Emergency
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Hub
import androidx.compose.material.icons.filled.Insights
import androidx.compose.material.icons.filled.Map
import androidx.compose.material.icons.filled.NotificationsActive
import androidx.compose.material.icons.filled.Security
import androidx.compose.material.icons.filled.Settings
import androidx.compose.ui.graphics.vector.ImageVector

sealed class Screen(
    val route: String,
    val title: String,
    val icon: ImageVector? = null,
    val isBottomNavDestination: Boolean = false
) {
    data object Splash : Screen(
        route = "splash",
        title = "Splash"
    )

    data object Home : Screen(
        route = "home",
        title = "Home",
        icon = Icons.Default.Home
    )

    data object Map : Screen(
        route = "map",
        title = "Map",
        icon = Icons.Default.Map,
        isBottomNavDestination = true
    )

    data object Overview : Screen(
        route = "overview",
        title = "Overview",
        icon = Icons.Default.Insights,
        isBottomNavDestination = true
    )

    data object Alerts : Screen(
        route = "alerts",
        title = "Alerts",
        icon = Icons.Default.NotificationsActive,
        isBottomNavDestination = true
    )

    data object Sos : Screen(
        route = "sos",
        title = "SOS",
        icon = Icons.Default.Emergency,
        isBottomNavDestination = true
    )

    data object Mesh : Screen(
        route = "mesh",
        title = "Mesh",
        icon = Icons.Default.Hub,
        isBottomNavDestination = true
    )

    data object Settings : Screen(
        route = "settings",
        title = "Settings",
        icon = Icons.Default.Settings
    )

    companion object {
        val bottomNavDestinations = listOf(Map, Overview, Alerts, Sos, Mesh)
    }
}
