package com.pukaar.android.ui.screens.onboarding

import androidx.compose.animation.core.animateDpAsState
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bluetooth
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Key
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Wifi
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pukaar.android.ui.components.GlowCard
import com.pukaar.android.ui.components.StatusDot
import com.pukaar.android.ui.theme.JetBrainsMonoFamily
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun OnboardingScreen(
    onFinish: () -> Unit,
    viewModel: OnboardingViewModel = hiltViewModel()
) {
    val pagerState = rememberPagerState(pageCount = { 3 })
    val setupState by viewModel.setupState.collectAsState()

    LaunchedEffect(pagerState.currentPage) {
        if (pagerState.currentPage == 2) {
            viewModel.startSetup()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(PukaarColors.BgVoid)
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        // Horizontal Pager
        HorizontalPager(
            state = pagerState,
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
        ) { page ->
            when (page) {
                0 -> PageUnderstand()
                1 -> PageSurvive()
                2 -> PageSetup(
                    setupState = setupState,
                    onGrantLocation = { viewModel.setLocationGranted(true) },
                    onGrantBluetooth = { viewModel.setBluetoothGranted(true) },
                    onGrantWifi = { viewModel.setWifiGranted(true) },
                    onLetsGo = { viewModel.completeOnboarding(onFinish) }
                )
            }
        }

        // Page Indicator Dots
        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.padding(vertical = 16.dp)
        ) {
            for (i in 0 until 3) {
                val isActive = pagerState.currentPage == i
                val width by animateDpAsState(
                    targetValue = if (isActive) 24.dp else 8.dp,
                    label = "indicator_width"
                )
                Box(
                    modifier = Modifier
                        .height(8.dp)
                        .width(width)
                        .clip(CircleShape)
                        .background(if (isActive) PukaarColors.AccentCyan else PukaarColors.TextSecondary.copy(alpha = 0.4f))
                )
            }
        }
    }
}

@Composable
private fun PageUnderstand() {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // Satellite Vector Canvas
        Canvas(modifier = Modifier.size(180.dp)) {
            val center = Offset(size.width / 2f, size.height / 2f)

            // Satellite body
            drawRoundRect(
                color = PukaarColors.AccentCyan,
                topLeft = Offset(center.x - 20.dp.toPx(), center.y - 12.dp.toPx()),
                size = Size(40.dp.toPx(), 24.dp.toPx()),
                cornerRadius = androidx.compose.ui.geometry.CornerRadius(4.dp.toPx(), 4.dp.toPx())
            )

            // Solar panels (Left and Right)
            drawRect(
                color = PukaarColors.AccentCyan.copy(alpha = 0.5f),
                topLeft = Offset(center.x - 55.dp.toPx(), center.y - 18.dp.toPx()),
                size = Size(30.dp.toPx(), 36.dp.toPx())
            )
            drawRect(
                color = PukaarColors.AccentCyan.copy(alpha = 0.5f),
                topLeft = Offset(center.x + 25.dp.toPx(), center.y - 18.dp.toPx()),
                size = Size(30.dp.toPx(), 36.dp.toPx())
            )

            // Signal Arcs
            for (r in 1..3) {
                drawArc(
                    color = PukaarColors.AccentCyan.copy(alpha = 1.0f / r),
                    startAngle = 45f,
                    sweepAngle = 90f,
                    useCenter = false,
                    topLeft = Offset(center.x - (25 * r).dp.toPx(), center.y + (10 * r).dp.toPx()),
                    size = Size((50 * r).dp.toPx(), (30 * r).dp.toPx()),
                    style = Stroke(width = 2.dp.toPx(), cap = StrokeCap.Round)
                )
            }
        }

        Spacer(modifier = Modifier.height(36.dp))

        Text(
            text = "WE PREDICT DISASTERS",
            fontFamily = RajdhaniFontFamily,
            fontWeight = FontWeight.Bold,
            fontSize = 32.sp,
            textAlign = TextAlign.Center,
            color = PukaarColors.TextPrimary
        )

        Spacer(modifier = Modifier.height(12.dp))

        Text(
            text = "AI-powered cyclone detection, classification, and trajectory prediction. Know before it hits.",
            fontSize = 16.sp,
            textAlign = TextAlign.Center,
            color = PukaarColors.TextSecondary,
            modifier = Modifier.width(280.dp)
        )
    }
}

@Composable
private fun PageSurvive() {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // Mesh Node Topology Canvas (5 nodes connected, 2 with BT, 2 with WiFi)
        Canvas(modifier = Modifier.size(180.dp)) {
            val center = Offset(size.width / 2f, size.height / 2f)
            val nodes = listOf(
                center,
                Offset(center.x - 50.dp.toPx(), center.y - 45.dp.toPx()),
                Offset(center.x + 50.dp.toPx(), center.y - 45.dp.toPx()),
                Offset(center.x - 55.dp.toPx(), center.y + 40.dp.toPx()),
                Offset(center.x + 55.dp.toPx(), center.y + 40.dp.toPx())
            )

            // Connections
            for (i in 1 until nodes.size) {
                drawLine(
                    color = PukaarColors.AccentCyan.copy(alpha = 0.4f),
                    start = center,
                    end = nodes[i],
                    strokeWidth = 2.dp.toPx()
                )
            }
            drawLine(
                color = PukaarColors.AccentCyan.copy(alpha = 0.25f),
                start = nodes[1],
                end = nodes[2],
                strokeWidth = 1.dp.toPx()
            )
            drawLine(
                color = PukaarColors.AccentCyan.copy(alpha = 0.25f),
                start = nodes[3],
                end = nodes[4],
                strokeWidth = 1.dp.toPx()
            )

            // Node Circles & Labels
            nodes.forEachIndexed { index, node ->
                val color = if (index == 0) PukaarColors.AccentCyan else PukaarColors.AccentGreen
                drawCircle(
                    color = color,
                    radius = if (index == 0) 14.dp.toPx() else 12.dp.toPx(),
                    center = node
                )

                // Label BT / WiFi / ROOT
                val label = when (index) {
                    0 -> "ROOT"
                    1, 2 -> "BT"
                    else -> "WIFI"
                }
                drawContext.canvas.nativeCanvas.apply {
                    val paint = android.graphics.Paint().apply {
                        this.color = android.graphics.Color.BLACK
                        textSize = 8.sp.toPx()
                        isFakeBoldText = true
                        textAlign = android.graphics.Paint.Align.CENTER
                        isAntiAlias = true
                    }
                    drawText(label, node.x, node.y + 3.dp.toPx(), paint)
                }
            }
        }

        Spacer(modifier = Modifier.height(36.dp))

        Text(
            text = "WARNINGS THAT SURVIVE",
            fontFamily = RajdhaniFontFamily,
            fontWeight = FontWeight.Bold,
            fontSize = 32.sp,
            textAlign = TextAlign.Center,
            color = PukaarColors.TextPrimary
        )

        Spacer(modifier = Modifier.height(12.dp))

        Text(
            text = "When internet fails, warnings travel through Bluetooth and Wi-Fi Aware mesh. Har pukar, kisi tak.",
            fontSize = 16.sp,
            textAlign = TextAlign.Center,
            color = PukaarColors.TextSecondary,
            modifier = Modifier.width(280.dp)
        )
    }
}

@Composable
private fun PageSetup(
    setupState: OnboardingSetupState,
    onGrantLocation: () -> Unit,
    onGrantBluetooth: () -> Unit,
    onGrantWifi: () -> Unit,
    onLetsGo: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.SpaceBetween,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "SETTING UP PUKAAR",
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 28.sp,
                color = PukaarColors.TextPrimary
            )
            Spacer(modifier = Modifier.height(24.dp))

            // Step List
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                // Step 1: Keystore Identity
                SetupStepRow(
                    label = if (setupState.keyGenState == SetupStepState.SUCCESS) "Keys secured in Keystore" else "Generating device identity...",
                    state = setupState.keyGenState
                )

                // Step 2: Server Registration
                SetupStepRow(
                    label = if (setupState.serverRegState == SetupStepState.SUCCESS) "Registered with server" else "Registering with server...",
                    state = setupState.serverRegState
                )

                Spacer(modifier = Modifier.height(12.dp))

                // Step 3: Permissions
                if (setupState.keyGenState == SetupStepState.SUCCESS) {
                    PermissionActionRow(
                        label = "LOCATION ACCESS",
                        isGranted = setupState.locationGranted,
                        onGrant = onGrantLocation
                    )

                    PermissionActionRow(
                        label = "BLUETOOTH MESH",
                        isGranted = setupState.bluetoothGranted,
                        onGrant = onGrantBluetooth
                    )

                    PermissionActionRow(
                        label = "WI-FI AWARE NEARBY",
                        isGranted = setupState.wifiGranted,
                        onGrant = onGrantWifi
                    )
                }
            }
        }

        // LET'S GO Button
        Button(
            onClick = onLetsGo,
            enabled = setupState.canProceed,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = PukaarColors.AccentCyan,
                disabledContainerColor = PukaarColors.BgElevated
            ),
            shape = RoundedCornerShape(12.dp)
        ) {
            Text(
                text = "LET'S GO",
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 20.sp,
                letterSpacing = 1.sp,
                color = if (setupState.canProceed) PukaarColors.BgVoid else PukaarColors.TextSecondary
            )
        }
    }
}

@Composable
private fun SetupStepRow(
    label: String,
    state: SetupStepState
) {
    GlowCard(
        glowColor = if (state == SetupStepState.SUCCESS) PukaarColors.AccentGreen else PukaarColors.AccentCyan,
        cornerRadius = 8.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = label,
                fontFamily = JetBrainsMonoFamily,
                fontSize = 12.sp,
                color = PukaarColors.TextPrimary
            )

            when (state) {
                SetupStepState.PENDING -> StatusDot(color = PukaarColors.TextSecondary)
                SetupStepState.IN_PROGRESS -> StatusDot(color = PukaarColors.AccentCyan)
                SetupStepState.SUCCESS -> Icon(Icons.Default.Check, contentDescription = null, tint = PukaarColors.AccentGreen, modifier = Modifier.size(18.dp))
                SetupStepState.FAILED -> Icon(Icons.Default.Close, contentDescription = null, tint = PukaarColors.AccentRed, modifier = Modifier.size(18.dp))
            }
        }
    }
}

@Composable
private fun PermissionActionRow(
    label: String,
    isGranted: Boolean,
    onGrant: () -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            fontFamily = JetBrainsMonoFamily,
            fontSize = 11.sp,
            color = PukaarColors.TextSecondary
        )

        if (isGranted) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                Icon(Icons.Default.Check, contentDescription = null, tint = PukaarColors.AccentGreen, modifier = Modifier.size(16.dp))
                Text(text = "GRANTED", fontFamily = JetBrainsMonoFamily, fontSize = 10.sp, color = PukaarColors.AccentGreen)
            }
        } else {
            OutlinedButton(
                onClick = onGrant,
                shape = RoundedCornerShape(6.dp),
                border = BorderStroke(1.dp, PukaarColors.AccentCyan),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = PukaarColors.AccentCyan)
            ) {
                Text(text = "GRANT", fontFamily = JetBrainsMonoFamily, fontSize = 10.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}
