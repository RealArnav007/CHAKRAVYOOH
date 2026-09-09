package com.pukaar.android.ui.screens.splash

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pukaar.android.ui.theme.JetBrainsMonoFamily
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily
import kotlinx.coroutines.delay

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

    // Cyclone Rotation Animation (1 rotation per 3s linear)
    val infiniteTransition = rememberInfiniteTransition(label = "cyclone_spin")
    val rotationAngle by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 3000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "rotation"
    )

    // Text Slide up + Fade in (600ms, EaseOut, delayed 400ms)
    val textAlpha = remember { Animatable(0f) }
    val textOffsetY = remember { Animatable(30f) }

    LaunchedEffect(Unit) {
        delay(400)
        textAlpha.animateTo(1f, animationSpec = tween(600, easing = FastOutSlowInEasing))
    }
    LaunchedEffect(Unit) {
        delay(400)
        textOffsetY.animateTo(0f, animationSpec = tween(600, easing = FastOutSlowInEasing))
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(PukaarColors.BgVoid),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            // Animated Cyclone Canvas (300x300dp)
            Canvas(modifier = Modifier.size(300.dp)) {
                val center = Offset(size.width / 2f, size.height / 2f)
                val alphas = listOf(1.0f, 0.8f, 0.6f, 0.4f, 0.2f)
                val baseRadius = size.minDimension / 2.2f

                // 5 Concentric Arcs offset by 72 deg
                for (i in 0 until 5) {
                    val arcRadius = baseRadius * (0.35f + (i * 0.15f))
                    val startAngle = rotationAngle + (i * 72f)
                    val alpha = alphas[i]

                    drawArc(
                        color = PukaarColors.AccentCyan.copy(alpha = alpha),
                        startAngle = startAngle,
                        sweepAngle = 210f,
                        useCenter = false,
                        topLeft = Offset(center.x - arcRadius, center.y - arcRadius),
                        size = Size(arcRadius * 2, arcRadius * 2),
                        style = Stroke(width = 3.dp.toPx(), cap = StrokeCap.Round)
                    )
                }

                // Center Circle: 12dp radius AccentCyan + 4dp radius AccentRed inside
                drawCircle(
                    color = PukaarColors.AccentCyan,
                    radius = 12.dp.toPx(),
                    center = center
                )
                drawCircle(
                    color = PukaarColors.AccentRed,
                    radius = 4.dp.toPx(),
                    center = center
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Animated Typography
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier
                    .offset(y = textOffsetY.value.dp)
                    .alpha(textAlpha.value)
            ) {
                Text(
                    text = "PUKAAR",
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 52.sp,
                    letterSpacing = 0.15.em,
                    color = PukaarColors.TextPrimary
                )

                Text(
                    text = "पुकार",
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 20.sp,
                    letterSpacing = 0.08.em,
                    color = PukaarColors.TextSecondary
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "HAR PUKAR, KISI TAK",
                    fontFamily = JetBrainsMonoFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 11.sp,
                    letterSpacing = 0.2.em,
                    color = PukaarColors.AccentCyan
                )
            }
        }
    }
}
