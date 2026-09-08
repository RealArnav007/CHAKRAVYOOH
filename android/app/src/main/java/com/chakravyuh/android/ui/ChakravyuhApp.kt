package com.chakravyuh.android.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.chakravyuh.android.ui.navigation.BottomNavigationBar
import com.chakravyuh.android.ui.navigation.ChakravyuhNavHost
import com.chakravyuh.android.ui.navigation.Screen
import com.chakravyuh.android.ui.theme.ChakravyuhBackground

/**
 * Root Composable scaffold hosting the NavHost and bottom navigation bar.
 */
@Composable
fun ChakravyuhApp() {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    val showBottomBar = currentRoute != Screen.Splash.route

    Scaffold(
        modifier = Modifier
            .fillMaxSize()
            .background(ChakravyuhBackground),
        containerColor = ChakravyuhBackground,
        bottomBar = {
            if (showBottomBar) {
                BottomNavigationBar(navController = navController)
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            ChakravyuhNavHost(navController = navController)
        }
    }
}
