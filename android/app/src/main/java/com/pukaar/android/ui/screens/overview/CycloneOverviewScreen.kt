package com.pukaar.android.ui.screens.overview

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Text
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pukaar.android.domain.model.CycloneIntelligence
import com.pukaar.android.domain.model.CycloneStage
import com.pukaar.android.domain.model.IntensityLevel
import com.pukaar.android.domain.model.RiskLevel
import com.pukaar.android.ui.components.ConfidenceBar
import com.pukaar.android.ui.components.DataLabel
import com.pukaar.android.ui.components.GlowCard
import com.pukaar.android.ui.components.StatusDot
import com.pukaar.android.ui.theme.JetBrainsMonoFamily
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily
import java.time.Instant

@Composable
fun CycloneOverviewScreen(
    viewModel: OverviewViewModel = hiltViewModel(),
    onNavigateToSettings: () -> Unit = {}
) {
    val state by viewModel.state.collectAsState()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(PukaarColors.BgVoid)
    ) {
        if (state.isLoading && state.intelligence == null) {
            RadarScanOverlay(text = "SCANNING FOR CYCLONE INTELLIGENCE")
        } else if (state.intelligence == null) {
            RadarScanOverlay(text = "NO ACTIVE CYCLONE DETECTED")
        } else {
            val intelligence = state.intelligence!!
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // 1. Header & Live Indicator
                item {
                    OverviewHeader(
                        cycloneId = intelligence.cycloneId,
                        stage = intelligence.classificationStage,
                        webSocketConnected = state.webSocketConnected
                    )
                }

                // 2. 2x2 Data Grid
                item {
                    OverviewDataGrid(intelligence = intelligence)
                }

                // 3. Operational Confidence Breakdown
                item {
                    OperationalConfidenceBreakdown(intelligence = intelligence)
                }

                // 4. Intelligence Freshness Card
                item {
                    FreshnessCard(intelligence = intelligence)
                }

                item {
                    Spacer(modifier = Modifier.height(24.dp))
                }
            }
        }
    }
}

@Composable
private fun OverviewHeader(
    cycloneId: String,
    stage: CycloneStage,
    webSocketConnected: Boolean
) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = cycloneId,
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 28.sp,
                color = PukaarColors.TextPrimary
            )

            StageGlowPill(stage = stage)
        }

        Spacer(modifier = Modifier.height(8.dp))

        HorizontalDivider(
            color = PukaarColors.AccentCyan.copy(alpha = 0.4f),
            thickness = 1.dp
        )

        Spacer(modifier = Modifier.height(8.dp))

        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            if (webSocketConnected) {
                StatusDot(color = PukaarColors.AccentGreen)
                Text(
                    text = "LIVE FEED ACTIVE",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = PukaarColors.AccentGreen
                )
            } else {
                StatusDot(color = PukaarColors.TextSecondary)
                Text(
                    text = "DISCONNECTED",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 11.sp,
                    color = PukaarColors.TextSecondary
                )
            }
        }
    }
}

@Composable
private fun StageGlowPill(stage: CycloneStage) {
    val (color, label) = when (stage) {
        CycloneStage.DEVELOPING_DISTURBANCE -> Pair(PukaarColors.AccentCyan, "DISTURBANCE")
        CycloneStage.TROPICAL_DEPRESSION -> Pair(PukaarColors.AccentYellow, "DEPRESSION")
        CycloneStage.MATURE_TROPICAL_CYCLONE -> Pair(PukaarColors.AccentRed, "MATURE CYCLONE")
        CycloneStage.WEAKENING_SYSTEM -> Pair(PukaarColors.AccentAmber, "WEAKENING")
        CycloneStage.POST_TROPICAL_REMNANT -> Pair(PukaarColors.AccentGreen, "REMNANT")
    }

    GlowCard(
        glowColor = color,
        cornerRadius = 8.dp,
        modifier = Modifier.padding(vertical = 2.dp)
    ) {
        Text(
            text = label,
            fontFamily = JetBrainsMonoFamily,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
            color = color
        )
    }
}

@Composable
private fun OverviewDataGrid(intelligence: CycloneIntelligence) {
    val operationalConf = calculateOperationalConfidence(intelligence)
    val stageFormatted = intelligence.classificationStage.name.replace("_", "\n")

    val intensityRiskLevel = when (intelligence.intensityLevel) {
        IntensityLevel.EXTREME -> RiskLevel.EXTREME
        IntensityLevel.HIGH -> RiskLevel.HIGH
        IntensityLevel.MODERATE -> RiskLevel.MODERATE
        IntensityLevel.LOW -> RiskLevel.LOW
    }
    val intensityColor = PukaarColors.forRiskLevel(intensityRiskLevel)

    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // Row 1: Cell A & Cell B
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Cell A: Classification
            GlowCard(
                glowColor = PukaarColors.AccentCyan,
                modifier = Modifier
                    .weight(1f)
                    .height(170.dp)
            ) {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.SpaceBetween
                ) {
                    DataLabel(
                        label = "STAGE",
                        value = stageFormatted,
                        valueColor = PukaarColors.TextPrimary
                    )
                    ConfidenceBar(
                        label = "CLASS CONFIDENCE",
                        progress = intelligence.classificationConfidence.toFloat(),
                        indicatorColor = PukaarColors.AccentCyan
                    )
                }
            }

            // Cell B: Intensity
            GlowCard(
                glowColor = intensityColor,
                modifier = Modifier
                    .weight(1f)
                    .height(170.dp)
            ) {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.SpaceBetween
                ) {
                    DataLabel(
                        label = "INTENSITY",
                        value = intelligence.intensityLevel.name,
                        valueColor = intensityColor
                    )
                    ConfidenceBar(
                        label = "CONFIDENCE",
                        progress = intelligence.intensityConfidence.toFloat(),
                        indicatorColor = intensityColor
                    )
                }
            }
        }

        // Row 2: Cell C & Cell D
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Cell C: Movement
            GlowCard(
                glowColor = PukaarColors.AccentAmber,
                modifier = Modifier
                    .weight(1f)
                    .height(170.dp)
            ) {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.SpaceBetween
                ) {
                    DataLabel(
                        label = "HEADING",
                        value = intelligence.heading,
                        valueColor = PukaarColors.AccentAmber
                    )
                    Text(
                        text = "FORECAST: ${intelligence.forecastHours}H",
                        fontFamily = JetBrainsMonoFamily,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = PukaarColors.TextSecondary
                    )
                }
            }

            // Cell D: Prediction
            GlowCard(
                glowColor = PukaarColors.AccentCyan,
                modifier = Modifier
                    .weight(1f)
                    .height(170.dp)
            ) {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.SpaceBetween
                ) {
                    DataLabel(
                        label = "PRED CONF",
                        value = "${(intelligence.predictionConfidence * 100).toInt()}%",
                        valueColor = PukaarColors.AccentCyan
                    )
                    ConfidenceBar(
                        label = "OPERATIONAL",
                        progress = operationalConf,
                        indicatorColor = PukaarColors.AccentCyan
                    )
                    Text(
                        text = "±${intelligence.uncertaintyRadiusKm.toInt()} KM",
                        fontFamily = JetBrainsMonoFamily,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = PukaarColors.AccentRed
                    )
                }
            }
        }
    }
}

@Composable
private fun OperationalConfidenceBreakdown(intelligence: CycloneIntelligence) {
    val aiConf = intelligence.predictionConfidence.toFloat()
    val freshnessScore = if (evaluateFreshness(intelligence.validUntil) == FreshnessState.VALID) 0.95f else 0.50f
    val operationalScore = (aiConf * 0.7f + freshnessScore * 0.3f)

    GlowCard(
        glowColor = PukaarColors.AccentCyan,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = "OPERATIONAL CONFIDENCE",
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 16.sp,
                letterSpacing = 1.sp,
                color = PukaarColors.TextPrimary
            )

            ConfidenceBar(
                label = "AI CONFIDENCE",
                progress = aiConf,
                indicatorColor = PukaarColors.AccentAmber
            )

            ConfidenceBar(
                label = "DATA FRESHNESS",
                progress = freshnessScore,
                indicatorColor = PukaarColors.AccentAmber
            )

            ConfidenceBar(
                label = "OPERATIONAL",
                progress = operationalScore,
                indicatorColor = PukaarColors.AccentCyan
            )
        }
    }
}

@Composable
private fun FreshnessCard(intelligence: CycloneIntelligence) {
    val freshness = evaluateFreshness(intelligence.validUntil)
    val (pillBg, pillText, pillLabel) = when (freshness) {
        FreshnessState.VALID -> Triple(PukaarColors.AccentGreen.copy(alpha = 0.2f), PukaarColors.AccentGreen, "VALID")
        FreshnessState.STALE -> Triple(PukaarColors.AccentAmber.copy(alpha = 0.2f), PukaarColors.AccentAmber, "STALE")
        FreshnessState.EXPIRED -> Triple(PukaarColors.AccentRed.copy(alpha = 0.2f), PukaarColors.AccentRed, "EXPIRED")
    }

    GlowCard(
        glowColor = pillText,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "INTELLIGENCE FRESHNESS",
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp,
                    letterSpacing = 1.sp,
                    color = PukaarColors.TextPrimary
                )

                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(12.dp))
                        .background(pillBg)
                        .border(1.dp, pillText.copy(alpha = 0.7f), RoundedCornerShape(12.dp))
                        .padding(horizontal = 12.dp, vertical = 4.dp)
                ) {
                    Text(
                        text = pillLabel,
                        fontFamily = JetBrainsMonoFamily,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        color = pillText
                    )
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text(
                        text = "GENERATED",
                        fontFamily = JetBrainsMonoFamily,
                        fontSize = 10.sp,
                        color = PukaarColors.TextSecondary
                    )
                    Text(
                        text = formatTimestamp(intelligence.generatedAt),
                        fontFamily = JetBrainsMonoFamily,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = PukaarColors.TextPrimary
                    )
                }

                Column(horizontalAlignment = Alignment.End) {
                    Text(
                        text = "VALID UNTIL",
                        fontFamily = JetBrainsMonoFamily,
                        fontSize = 10.sp,
                        color = PukaarColors.TextSecondary
                    )
                    Text(
                        text = formatTimestamp(intelligence.validUntil),
                        fontFamily = JetBrainsMonoFamily,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = PukaarColors.TextPrimary
                    )
                }
            }
        }
    }
}

private enum class FreshnessState {
    VALID, STALE, EXPIRED
}

private fun evaluateFreshness(validUntil: String): FreshnessState {
    return try {
        val expiry = Instant.parse(validUntil).toEpochMilli()
        val now = System.currentTimeMillis()
        when {
            now <= expiry -> FreshnessState.VALID
            now - expiry < 3 * 3600 * 1000L -> FreshnessState.STALE
            else -> FreshnessState.EXPIRED
        }
    } catch (e: Exception) {
        FreshnessState.VALID
    }
}

private fun calculateOperationalConfidence(intelligence: CycloneIntelligence): Float {
    val freshnessWeight = if (evaluateFreshness(intelligence.validUntil) == FreshnessState.VALID) 1.0f else 0.5f
    val operational = (intelligence.predictionConfidence.toFloat() * 0.7f + freshnessWeight * 0.3f)
    return operational.coerceIn(0f, 1f)
}

private fun formatTimestamp(iso: String): String {
    return try {
        val instant = Instant.parse(iso)
        iso.replace("T", " ").replace("Z", "")
    } catch (e: Exception) {
        iso
    }
}

@Composable
private fun RadarScanOverlay(text: String) {
    val transition = rememberInfiniteTransition(label = "radar_sweep_overview")
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
        Canvas(modifier = Modifier.size(240.dp)) {
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
            modifier = Modifier.padding(top = 280.dp)
        ) {
            Text(
                text = text,
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                letterSpacing = 2.sp,
                color = PukaarColors.AccentCyan
            )
        }
    }
}
