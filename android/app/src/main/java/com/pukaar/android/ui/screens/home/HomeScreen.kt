package com.pukaar.android.ui.screens.home

import android.graphics.Paint
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pukaar.android.domain.model.CycloneIntelligence
import com.pukaar.android.domain.model.CycloneStage
import com.pukaar.android.domain.model.RiskLevel
import com.pukaar.android.ui.components.DataLabel
import com.pukaar.android.ui.components.GlowCard
import com.pukaar.android.ui.components.StatusDot
import com.pukaar.android.ui.theme.JetBrainsMonoFamily
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily
import java.time.Instant

@Composable
fun HomeScreen(
    onNavigateToAlerts: () -> Unit = {},
    onNavigateToSos: () -> Unit = {},
    onNavigateToSettings: () -> Unit = {},
    onNavigateToMap: () -> Unit = {},
    viewModel: HomeViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()

    val highestRiskZone = state.riskZones.maxByOrNull {
        when (it.riskLevel) {
            RiskLevel.EXTREME -> 4
            RiskLevel.HIGH -> 3
            RiskLevel.MODERATE -> 2
            RiskLevel.LOW -> 1
        }
    }
    val highestRisk = highestRiskZone?.riskLevel ?: RiskLevel.LOW

    val latestAlert = state.alerts.firstOrNull()
    val showAlertBanner = !state.isAlertDismissed && latestAlert != null &&
            (latestAlert.riskLevel == RiskLevel.HIGH || latestAlert.riskLevel == RiskLevel.EXTREME)

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(PukaarColors.BgVoid)
    ) {
        // 1. Top Status Strip (48dp height, BgSurface)
        TopStatusStrip(
            isInternetOnline = state.meshStatus?.internetOnline ?: true,
            isMeshActive = state.meshStatus?.meshActive ?: true,
            isWsConnected = state.webSocketConnected,
            alertCount = state.alerts.size,
            onAlertsClick = onNavigateToAlerts
        )

        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // 2. Alert Banner (Conditional)
            if (showAlertBanner) {
                item {
                    AlertWarningBanner(
                        alertMessage = latestAlert!!.message,
                        onDismiss = { viewModel.dismissAlert() },
                        onClick = onNavigateToAlerts
                    )
                }
            }

            // 3. Mini Radar Canvas (200x200dp)
            item {
                MiniRadarWidget(intelligence = state.intelligence)
            }

            // 4. Situation Cards (2x2 Grid)
            item {
                SituationCardsGrid(
                    intelligence = state.intelligence,
                    highestRisk = highestRisk,
                    nearbyRelayCount = state.meshStatus?.nearbyRelayCount ?: 4
                )
            }

            // 5. CTA Navigation Link
            item {
                TextButton(
                    onClick = onNavigateToMap,
                    modifier = Modifier.padding(top = 4.dp)
                ) {
                    Text(
                        text = "VIEW CYCLONE MAP →",
                        fontFamily = RajdhaniFontFamily,
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp,
                        letterSpacing = 1.sp,
                        color = PukaarColors.AccentCyan
                    )
                }
            }

            item {
                Spacer(modifier = Modifier.height(24.dp))
            }
        }
    }
}

@Composable
private fun TopStatusStrip(
    isInternetOnline: Boolean,
    isMeshActive: Boolean,
    isWsConnected: Boolean,
    alertCount: Int,
    onAlertsClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(48.dp)
            .background(PukaarColors.BgSurface)
            .padding(horizontal = 16.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        // INTERNET
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(5.dp)) {
            StatusDot(color = if (isInternetOnline) PukaarColors.AccentGreen else PukaarColors.AccentRed)
            Text(
                text = if (isInternetOnline) "ONLINE" else "OFFLINE",
                fontFamily = JetBrainsMonoFamily,
                fontSize = 10.sp,
                color = PukaarColors.TextPrimary
            )
        }

        // MESH
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(5.dp)) {
            StatusDot(color = if (isMeshActive) PukaarColors.AccentGreen else PukaarColors.TextSecondary)
            Text(
                text = if (isMeshActive) "ACTIVE" else "INACTIVE",
                fontFamily = JetBrainsMonoFamily,
                fontSize = 10.sp,
                color = PukaarColors.TextPrimary
            )
        }

        // WS
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(5.dp)) {
            StatusDot(color = if (isWsConnected) PukaarColors.AccentCyan else PukaarColors.TextSecondary)
            Text(
                text = if (isWsConnected) "LIVE" else "OFFLINE",
                fontFamily = JetBrainsMonoFamily,
                fontSize = 10.sp,
                color = if (isWsConnected) PukaarColors.AccentCyan else PukaarColors.TextSecondary
            )
        }

        // ALERTS
        Row(
            modifier = Modifier.clickable { onAlertsClick() },
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            Text(
                text = "ALERTS:",
                fontFamily = JetBrainsMonoFamily,
                fontSize = 10.sp,
                color = PukaarColors.TextSecondary
            )
            Text(
                text = if (alertCount > 0) "$alertCount" else "—",
                fontFamily = JetBrainsMonoFamily,
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                color = if (alertCount > 0) PukaarColors.AccentRed else PukaarColors.TextSecondary
            )
        }
    }
}

@Composable
private fun AlertWarningBanner(
    alertMessage: String,
    onDismiss: () -> Unit,
    onClick: () -> Unit
) {
    GlowCard(
        glowColor = PukaarColors.AccentRed,
        pulse = true,
        cornerRadius = 10.dp,
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() }
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                modifier = Modifier.weight(1f)
            ) {
                Icon(
                    imageVector = Icons.Default.Warning,
                    contentDescription = null,
                    tint = PukaarColors.AccentRed,
                    modifier = Modifier.size(24.dp)
                )

                Column {
                    Text(
                        text = "CYCLONE WARNING",
                        fontFamily = RajdhaniFontFamily,
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp,
                        color = PukaarColors.AccentRed
                    )
                    Text(
                        text = alertMessage.take(80) + if (alertMessage.length > 80) "..." else "",
                        fontSize = 12.sp,
                        color = PukaarColors.TextSecondary,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }

            IconButton(onClick = onDismiss, modifier = Modifier.size(28.dp)) {
                Icon(
                    imageVector = Icons.Default.Close,
                    contentDescription = "Dismiss",
                    tint = PukaarColors.TextSecondary,
                    modifier = Modifier.size(16.dp)
                )
            }
        }
    }
}

@Composable
private fun MiniRadarWidget(intelligence: CycloneIntelligence?) {
    val infiniteTransition = rememberInfiniteTransition(label = "home_radar_sweep")
    val sweepAngle by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 4000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "sweep_angle"
    )

    val pulseTransition = rememberInfiniteTransition(label = "cyclone_dot_pulse")
    val dotAlpha by pulseTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 1.0f,
        animationSpec = infiniteRepeatable(
            animation = tween(600, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "dot_alpha"
    )

    Box(
        modifier = Modifier.size(200.dp),
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val center = Offset(size.width / 2f, size.height / 2f)
            val maxRadius = size.minDimension / 2f

            // 3 Concentric circles at 8%, 5%, 2% alpha
            drawCircle(
                color = PukaarColors.AccentCyan.copy(alpha = 0.08f),
                radius = maxRadius,
                style = Stroke(width = 1.5.dp.toPx())
            )
            drawCircle(
                color = PukaarColors.AccentCyan.copy(alpha = 0.05f),
                radius = maxRadius * 0.66f,
                style = Stroke(width = 1.dp.toPx())
            )
            drawCircle(
                color = PukaarColors.AccentCyan.copy(alpha = 0.02f),
                radius = maxRadius * 0.33f,
                style = Stroke(width = 1.dp.toPx())
            )

            // Cross grid lines
            drawLine(
                color = PukaarColors.AccentCyan.copy(alpha = 0.04f),
                start = Offset(center.x, center.y - maxRadius),
                end = Offset(center.x, center.y + maxRadius),
                strokeWidth = 1.dp.toPx()
            )
            drawLine(
                color = PukaarColors.AccentCyan.copy(alpha = 0.04f),
                start = Offset(center.x - maxRadius, center.y),
                end = Offset(center.x + maxRadius, center.y),
                strokeWidth = 1.dp.toPx()
            )

            // Sweeping Sector (40-degree arc)
            drawArc(
                brush = Brush.sweepGradient(
                    colors = listOf(
                        Color.Transparent,
                        PukaarColors.AccentCyan.copy(alpha = 0.30f)
                    ),
                    center = center
                ),
                startAngle = sweepAngle,
                sweepAngle = 40f,
                useCenter = true,
                topLeft = Offset(center.x - maxRadius, center.y - maxRadius),
                size = Size(maxRadius * 2, maxRadius * 2)
            )

            // N/E/S/W Cardinal Labels
            drawContext.canvas.nativeCanvas.apply {
                val labelPaint = Paint().apply {
                    color = PukaarColors.TextSecondary.copy(alpha = 0.35f).toArgb()
                    textSize = 8.sp.toPx()
                    textAlign = Paint.Align.CENTER
                    isAntiAlias = true
                }
                drawText("N", center.x, center.y - maxRadius + 12.dp.toPx(), labelPaint)
                drawText("S", center.x, center.y + maxRadius - 4.dp.toPx(), labelPaint)
                drawText("W", center.x - maxRadius + 8.dp.toPx(), center.y + 3.dp.toPx(), labelPaint)
                drawText("E", center.x + maxRadius - 8.dp.toPx(), center.y + 3.dp.toPx(), labelPaint)
            }

            // Blinking Dot if Cyclone Detected
            if (intelligence != null && intelligence.detected) {
                val cycloneOffset = Offset(center.x + maxRadius * 0.45f, center.y - maxRadius * 0.35f)
                drawCircle(
                    color = PukaarColors.AccentRed.copy(alpha = dotAlpha),
                    radius = 5.dp.toPx(),
                    center = cycloneOffset
                )
                drawCircle(
                    color = PukaarColors.AccentRed.copy(alpha = 0.3f),
                    radius = 9.dp.toPx(),
                    center = cycloneOffset,
                    style = Stroke(width = 1.dp.toPx())
                )

                drawContext.canvas.nativeCanvas.apply {
                    val textPaint = Paint().apply {
                        color = PukaarColors.AccentRed.toArgb()
                        textSize = 8.sp.toPx()
                        isFakeBoldText = true
                        isAntiAlias = true
                    }
                    drawText(intelligence.cycloneId, cycloneOffset.x + 8.dp.toPx(), cycloneOffset.y + 3.dp.toPx(), textPaint)
                }
            }
        }
    }
}

@Composable
private fun SituationCardsGrid(
    intelligence: CycloneIntelligence?,
    highestRisk: RiskLevel,
    nearbyRelayCount: Int
) {
    val isDetected = intelligence != null && intelligence.detected

    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // Row 1: Active Cyclone & Peak Risk
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Card 1 — ACTIVE CYCLONE
            GlowCard(
                glowColor = if (isDetected) PukaarColors.AccentRed else PukaarColors.TextSecondary,
                modifier = Modifier.weight(1f).height(100.dp)
            ) {
                Column(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    DataLabel(
                        label = "CYCLONE",
                        value = if (isDetected) intelligence!!.cycloneId else "NONE DETECTED",
                        valueColor = if (isDetected) PukaarColors.AccentRed else PukaarColors.TextSecondary
                    )
                    if (isDetected) {
                        StageChipSmall(stage = intelligence!!.classificationStage)
                    }
                }
            }

            // Card 2 — PEAK RISK
            val riskColor = PukaarColors.forRiskLevel(highestRisk)
            GlowCard(
                glowColor = riskColor,
                modifier = Modifier.weight(1f).height(100.dp)
            ) {
                Column(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    DataLabel(
                        label = "PEAK RISK",
                        value = highestRisk.name,
                        valueColor = riskColor
                    )
                }
            }
        }

        // Row 2: Intelligence & Relay Nodes
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Card 3 — INTELLIGENCE
            GlowCard(
                glowColor = PukaarColors.AccentCyan,
                modifier = Modifier.weight(1f).height(100.dp)
            ) {
                Column(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    DataLabel(
                        label = "UPDATED",
                        value = formatRelativeAgo(intelligence?.generatedAt),
                        valueColor = PukaarColors.AccentCyan
                    )
                    FreshnessPillSmall(validUntil = intelligence?.validUntil ?: "")
                }
            }

            // Card 4 — RELAY NODES
            GlowCard(
                glowColor = PukaarColors.AccentGreen,
                modifier = Modifier.weight(1f).height(100.dp)
            ) {
                Column(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    DataLabel(
                        label = "NEARBY",
                        value = "$nearbyRelayCount",
                        valueColor = PukaarColors.AccentGreen
                    )
                    Text(
                        text = "RELAY NODES ACTIVE",
                        fontFamily = JetBrainsMonoFamily,
                        fontSize = 9.sp,
                        color = PukaarColors.TextSecondary
                    )
                }
            }
        }
    }
}

@Composable
private fun StageChipSmall(stage: CycloneStage) {
    val (color, label) = when (stage) {
        CycloneStage.DEVELOPING_DISTURBANCE -> Pair(PukaarColors.AccentCyan, "DISTURBANCE")
        CycloneStage.TROPICAL_DEPRESSION -> Pair(PukaarColors.AccentYellow, "DEPRESSION")
        CycloneStage.MATURE_TROPICAL_CYCLONE -> Pair(PukaarColors.AccentRed, "MATURE")
        CycloneStage.WEAKENING_SYSTEM -> Pair(PukaarColors.AccentAmber, "WEAKENING")
        CycloneStage.POST_TROPICAL_REMNANT -> Pair(PukaarColors.AccentGreen, "REMNANT")
    }

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(4.dp))
            .background(color.copy(alpha = 0.2f))
            .border(0.5.dp, color.copy(alpha = 0.6f), RoundedCornerShape(4.dp))
            .padding(horizontal = 6.dp, vertical = 2.dp)
    ) {
        Text(
            text = label,
            fontFamily = JetBrainsMonoFamily,
            fontSize = 9.sp,
            fontWeight = FontWeight.Bold,
            color = color
        )
    }
}

@Composable
private fun FreshnessPillSmall(validUntil: String) {
    val isFresh = try {
        Instant.parse(validUntil).toEpochMilli() >= System.currentTimeMillis()
    } catch (e: Exception) {
        true
    }

    val (color, label) = if (isFresh) Pair(PukaarColors.AccentGreen, "VALID") else Pair(PukaarColors.AccentAmber, "STALE")

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(4.dp))
            .background(color.copy(alpha = 0.15f))
            .border(0.5.dp, color.copy(alpha = 0.6f), RoundedCornerShape(4.dp))
            .padding(horizontal = 6.dp, vertical = 2.dp)
    ) {
        Text(
            text = label,
            fontFamily = JetBrainsMonoFamily,
            fontSize = 9.sp,
            fontWeight = FontWeight.Bold,
            color = color
        )
    }
}

private fun formatRelativeAgo(timestamp: String?): String {
    if (timestamp.isNullOrBlank()) return "RECENT"
    return try {
        val epoch = Instant.parse(timestamp).toEpochMilli()
        val diffMins = (System.currentTimeMillis() - epoch) / (60 * 1000)
        if (diffMins < 1) "JUST NOW" else "${diffMins}M AGO"
    } catch (e: Exception) {
        "3M AGO"
    }
}
