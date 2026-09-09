package com.pukaar.android.ui.screens.alerts

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.expandVertically
import androidx.compose.animation.core.fadeIn
import androidx.compose.animation.core.fadeOut
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.shrinkVertically
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.material3.pulltorefresh.rememberPullToRefreshState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pukaar.android.domain.model.CycloneAlert
import com.pukaar.android.domain.model.VerificationStatus
import com.pukaar.android.ui.components.GlowCard
import com.pukaar.android.ui.components.RiskBadge
import com.pukaar.android.ui.theme.JetBrainsMonoFamily
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AlertFeedScreen(
    viewModel: AlertsViewModel = hiltViewModel(),
    onNavigateToSettings: () -> Unit = {}
) {
    val state by viewModel.state.collectAsState()
    val pullToRefreshState = rememberPullToRefreshState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(PukaarColors.BgVoid)
    ) {
        // TopAppBar (transparent, no elevation)
        TopAppBar(
            title = {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        text = "ALERTS",
                        fontFamily = RajdhaniFontFamily,
                        fontWeight = FontWeight.Bold,
                        fontSize = 22.sp,
                        letterSpacing = 1.sp,
                        color = PukaarColors.TextPrimary
                    )

                    if (state.alerts.isNotEmpty()) {
                        Box(
                            modifier = Modifier
                                .size(22.dp)
                                .clip(CircleShape)
                                .background(PukaarColors.AccentRed),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "${state.alerts.size}",
                                fontFamily = JetBrainsMonoFamily,
                                fontWeight = FontWeight.Bold,
                                fontSize = 11.sp,
                                color = Color.White
                            )
                        }
                    }
                }
            },
            actions = {
                IconButton(onClick = { viewModel.refresh() }) {
                    Icon(
                        imageVector = Icons.Default.Refresh,
                        contentDescription = "Refresh Alerts",
                        tint = PukaarColors.AccentCyan
                    )
                }
                IconButton(onClick = onNavigateToSettings) {
                    Icon(
                        imageVector = Icons.Default.Settings,
                        contentDescription = "Settings",
                        tint = PukaarColors.TextSecondary
                    )
                }
            },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = Color.Transparent,
                scrolledContainerColor = Color.Transparent
            )
        )

        PullToRefreshBox(
            isRefreshing = state.isLoading,
            onRefresh = { viewModel.refresh() },
            state = pullToRefreshState,
            modifier = Modifier.fillMaxSize()
        ) {
            if (state.alerts.isEmpty() && !state.isLoading) {
                EmptyAlertsState()
            } else {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(state.alerts, key = { it.alertId }) { alert ->
                        AlertCard(alert = alert)
                        HorizontalDivider(
                            color = PukaarColors.AccentCyan.copy(alpha = 0.15f),
                            thickness = 0.5.dp,
                            modifier = Modifier.padding(top = 12.dp)
                        )
                    }

                    item {
                        Spacer(modifier = Modifier.height(24.dp))
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun AlertCard(alert: CycloneAlert) {
    var expanded by remember { mutableStateOf(false) }
    val glowColor = PukaarColors.forRiskLevel(alert.riskLevel)

    GlowCard(
        glowColor = glowColor,
        cornerRadius = 12.dp,
        modifier = Modifier
            .fillMaxWidth()
            .clickable { expanded = !expanded }
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Top Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                RiskBadge(riskLevel = alert.riskLevel)

                Text(
                    text = "${alert.alertId}  v${alert.version}",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 11.sp,
                    color = PukaarColors.TextSecondary
                )
            }

            // Middle: Alert Message
            Text(
                text = alert.message,
                style = androidx.compose.material3.MaterialTheme.typography.bodyMedium,
                color = PukaarColors.TextPrimary,
                fontSize = 14.sp,
                maxLines = if (expanded) Int.MAX_VALUE else 2,
                overflow = TextOverflow.Ellipsis
            )

            if (alert.supersedes != null) {
                Text(
                    text = "Supersedes ${alert.supersedes}",
                    fontStyle = FontStyle.Italic,
                    fontSize = 11.sp,
                    color = PukaarColors.TextSecondary
                )
            }

            // Expanded content
            AnimatedVisibility(
                visible = expanded,
                enter = expandVertically() + fadeIn(),
                exit = shrinkVertically() + fadeOut()
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 6.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    if (alert.affectedZones.isNotEmpty()) {
                        Text(
                            text = "AFFECTED ZONES:",
                            fontFamily = JetBrainsMonoFamily,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            color = PukaarColors.TextSecondary
                        )

                        FlowRow(
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                            verticalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            alert.affectedZones.forEach { zone ->
                                Box(
                                    modifier = Modifier
                                        .clip(RoundedCornerShape(4.dp))
                                        .background(glowColor.copy(alpha = 0.15f))
                                        .border(0.5.dp, glowColor.copy(alpha = 0.6f), RoundedCornerShape(4.dp))
                                        .padding(horizontal = 6.dp, vertical = 2.dp)
                                ) {
                                    Text(
                                        text = zone,
                                        fontFamily = JetBrainsMonoFamily,
                                        fontSize = 10.sp,
                                        color = glowColor
                                    )
                                }
                            }
                        }
                    }

                    val sigPreview = if (alert.signature.length > 16) "${alert.signature.take(16)}..." else alert.signature
                    Text(
                        text = "SIG: $sigPreview",
                        fontFamily = JetBrainsMonoFamily,
                        fontSize = 10.sp,
                        color = PukaarColors.TextSecondary
                    )
                }
            }

            // Bottom Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "VALID UNTIL ${formatValidUntil(alert.validUntil)}",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 10.sp,
                    color = PukaarColors.TextSecondary
                )

                VerificationStatusChip(status = alert.verificationStatus)
            }
        }
    }
}

@Composable
private fun VerificationStatusChip(status: VerificationStatus) {
    val (bgColor, textColor, label) = when (status) {
        VerificationStatus.VERIFIED -> Triple(
            PukaarColors.AccentGreen.copy(alpha = 0.20f),
            PukaarColors.AccentGreen,
            "✓ VERIFIED"
        )
        VerificationStatus.UNVERIFIED -> Triple(
            PukaarColors.AccentYellow.copy(alpha = 0.20f),
            PukaarColors.AccentYellow,
            "? UNVERIFIED"
        )
        VerificationStatus.INVALID -> Triple(
            PukaarColors.AccentRed.copy(alpha = 0.20f),
            PukaarColors.AccentRed,
            "✗ INVALID"
        )
        VerificationStatus.PENDING -> Triple(
            PukaarColors.BgElevated,
            PukaarColors.TextSecondary,
            "◌ CHECKING"
        )
    }

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(6.dp))
            .background(bgColor)
            .border(1.dp, textColor.copy(alpha = 0.5f), RoundedCornerShape(6.dp))
            .padding(horizontal = 8.dp, vertical = 2.dp)
    ) {
        Text(
            text = label,
            fontFamily = JetBrainsMonoFamily,
            fontSize = 10.sp,
            fontWeight = FontWeight.Bold,
            color = textColor
        )
    }
}

private fun formatValidUntil(time: String): String {
    return time.replace("T", " ").replace("Z", "")
}

@Composable
private fun EmptyAlertsState() {
    val transition = rememberInfiniteTransition(label = "radar_empty_alerts")
    val angle by transition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(2500, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "radar_angle"
    )

    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.size(200.dp)) {
            val center = Offset(size.width / 2f, size.height / 2f)
            val maxRadius = size.minDimension / 2f

            drawCircle(
                color = PukaarColors.AccentCyan.copy(alpha = 0.05f),
                radius = maxRadius,
                style = Stroke(width = 1.5.dp.toPx())
            )
            drawCircle(
                color = PukaarColors.AccentCyan.copy(alpha = 0.03f),
                radius = maxRadius * 0.66f,
                style = Stroke(width = 1.5.dp.toPx())
            )
            drawCircle(
                color = PukaarColors.AccentCyan.copy(alpha = 0.01f),
                radius = maxRadius * 0.33f,
                style = Stroke(width = 1.5.dp.toPx())
            )

            drawArc(
                brush = Brush.sweepGradient(
                    colors = listOf(
                        Color.Transparent,
                        PukaarColors.AccentCyan.copy(alpha = 0.35f)
                    ),
                    center = center
                ),
                startAngle = angle,
                sweepAngle = 40f,
                useCenter = true,
                topLeft = Offset(center.x - maxRadius, center.y - maxRadius),
                size = Size(maxRadius * 2, maxRadius * 2)
            )
        }

        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(top = 240.dp)
        ) {
            Text(
                text = "NO ACTIVE ALERTS",
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                letterSpacing = 2.sp,
                color = PukaarColors.AccentCyan
            )
        }
    }
}
