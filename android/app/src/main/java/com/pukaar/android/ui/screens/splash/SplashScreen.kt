package com.pukaar.android.ui.screens.splash

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pukaar.android.ui.components.StatusDot
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily

@Composable
fun SplashScreen(
    onNavigateNext: (Boolean) -> Unit,
    viewModel: SplashViewModel = hiltViewModel()
) {
    val isReady by viewModel.isReady.collectAsState()
    val onboardingComplete by viewModel.isOnboardingComplete.collectAsState()

    LaunchedEffect(isReady) {
        if (isReady) {
            onNavigateNext(onboardingComplete)
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(PukaarColors.BgVoid),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier.padding(24.dp)
        ) {
            StatusDot(color = PukaarColors.AccentRed, modifier = Modifier.padding(bottom = 16.dp))

            Text(
                text = "PUKAAR",
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 54.sp,
                letterSpacing = 4.sp,
                color = PukaarColors.TextPrimary
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "OFFLINE MESH & RESILIENCE NETWORK",
                style = MaterialTheme.typography.labelSmall,
                color = PukaarColors.AccentCyan
            )

            Spacer(modifier = Modifier.height(32.dp))

            CircularProgressIndicator(
                color = PukaarColors.AccentCyan,
                strokeWidth = 2.dp
            )
        }
    }
}
