package com.chakravyuh.android.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.chakravyuh.android.ui.screens.alerts.AlertsScreen
import com.chakravyuh.android.ui.screens.home.HomeScreen
import com.chakravyuh.android.ui.screens.map.MapScreen
import com.chakravyuh.android.ui.screens.mesh.MeshScreen
import com.chakravyuh.android.ui.screens.overview.OverviewScreen
import com.chakravyuh.android.ui.screens.settings.SettingsScreen
import com.chakravyuh.android.ui.screens.sos.SosScreen
import com.chakravyuh.android.ui.screens.splash.SplashScreen

@Composable
fun ChakravyuhNavHost(
    navController: NavHostController,
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = navController,
        startDestination = Screen.Splash.route,
        modifier = modifier
    ) {
        // 1. Splash Destination
        composable(Screen.Splash.route) {
            SplashScreen(
                onNavigateToHome = {
                    navController.navigate(Screen.Home.route) {
                        popUpTo(Screen.Splash.route) { inclusive = true }
                    }
                }
            )
        }

        // 2. Home Destination
        composable(Screen.Home.route) {
            HomeScreen(
                onNavigateToAlerts = { navController.navigate(Screen.Alerts.route) },
                onNavigateToSos = { navController.navigate(Screen.Sos.route) },
                onNavigateToSettings = { navController.navigate(Screen.Settings.route) }
            )
        }

        // 3. Map Destination
        composable(Screen.Map.route) {
            MapScreen(
                onNavigateToSettings = { navController.navigate(Screen.Settings.route) }
            )
        }

        // 4. Overview Destination
        composable(Screen.Overview.route) {
            OverviewScreen(
                onNavigateToSettings = { navController.navigate(Screen.Settings.route) }
            )
        }

        // 5. Alerts Destination
        composable(Screen.Alerts.route) {
            AlertsScreen(
                onNavigateToSettings = { navController.navigate(Screen.Settings.route) }
            )
        }

        // 6. SOS Destination
        composable(Screen.Sos.route) {
            SosScreen(
                onNavigateToSettings = { navController.navigate(Screen.Settings.route) }
            )
        }

        // 7. Mesh Destination
        composable(Screen.Mesh.route) {
            MeshScreen(
                onNavigateToSettings = { navController.navigate(Screen.Settings.route) }
            )
        }

        // 8. Settings Destination
        composable(Screen.Settings.route) {
            SettingsScreen(
                onNavigateBack = { navController.popBackStack() }
            )
        }
    }
}
