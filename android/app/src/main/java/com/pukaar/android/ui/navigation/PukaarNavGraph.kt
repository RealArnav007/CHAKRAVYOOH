package com.pukaar.android.ui.navigation

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.pukaar.android.ui.screens.alerts.AlertsScreen
import com.pukaar.android.ui.screens.home.HomeScreen
import com.pukaar.android.ui.screens.map.MapScreen
import com.pukaar.android.ui.screens.mesh.MeshScreen
import com.pukaar.android.ui.screens.onboarding.OnboardingScreen
import com.pukaar.android.ui.screens.overview.OverviewScreen
import com.pukaar.android.ui.screens.settings.SettingsScreen
import com.pukaar.android.ui.screens.sos.SosScreen
import com.pukaar.android.ui.screens.splash.SplashScreen
import com.pukaar.android.ui.theme.PukaarColors

@Composable
fun PukaarNavGraph() {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    val bottomNavVisibleRoutes = listOf(
        Screen.Home.route,
        Screen.Map.route,
        Screen.Overview.route,
        Screen.Alerts.route,
        Screen.Sos.route,
        Screen.Mesh.route
    )

    val showBottomBar = currentRoute in bottomNavVisibleRoutes

    Scaffold(
        modifier = Modifier
            .fillMaxSize()
            .background(PukaarColors.BgVoid),
        containerColor = PukaarColors.BgVoid,
        bottomBar = {
            if (showBottomBar) {
                BottomNavBar(navController = navController)
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            NavHost(
                navController = navController,
                startDestination = Screen.Splash.route
            ) {
                // 1. Splash
                composable(Screen.Splash.route) {
                    SplashScreen(
                        onNavigateNext = { onboardingComplete ->
                            val dest = if (onboardingComplete) Screen.Home.route else Screen.Onboarding.route
                            navController.navigate(dest) {
                                popUpTo(Screen.Splash.route) { inclusive = true }
                            }
                        }
                    )
                }

                // 2. Onboarding
                composable(Screen.Onboarding.route) {
                    OnboardingScreen(
                        onFinish = {
                            navController.navigate(Screen.Home.route) {
                                popUpTo(Screen.Onboarding.route) { inclusive = true }
                            }
                        }
                    )
                }

                // 3. Home
                composable(Screen.Home.route) {
                    HomeScreen(
                        onNavigateToAlerts = { navController.navigate(Screen.Alerts.route) },
                        onNavigateToSos = { navController.navigate(Screen.Sos.route) },
                        onNavigateToSettings = { navController.navigate(Screen.Settings.route) }
                    )
                }

                // 4. Map
                composable(Screen.Map.route) {
                    MapScreen(
                        onNavigateToSettings = { navController.navigate(Screen.Settings.route) }
                    )
                }

                // 5. Overview
                composable(Screen.Overview.route) {
                    OverviewScreen(
                        onNavigateToSettings = { navController.navigate(Screen.Settings.route) }
                    )
                }

                // 6. Alerts
                composable(Screen.Alerts.route) {
                    AlertsScreen(
                        onNavigateToSettings = { navController.navigate(Screen.Settings.route) }
                    )
                }

                // 7. SOS
                composable(Screen.Sos.route) {
                    SosScreen(
                        onNavigateToSettings = { navController.navigate(Screen.Settings.route) }
                    )
                }

                // 8. Mesh
                composable(Screen.Mesh.route) {
                    MeshScreen(
                        onNavigateToSettings = { navController.navigate(Screen.Settings.route) }
                    )
                }

                // 9. Settings
                composable(Screen.Settings.route) {
                    SettingsScreen(
                        onNavigateBack = { navController.popBackStack() }
                    )
                }
            }
        }
    }
}
