package com.pukaar.android.ui.screens.overview

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pukaar.android.domain.model.RiskLevel
import com.pukaar.android.ui.components.ConfidenceBar
import com.pukaar.android.ui.components.DataLabel
import com.pukaar.android.ui.components.GlowCard
import com.pukaar.android.ui.components.RiskBadge
import com.pukaar.android.ui.components.StatusDot
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily

@Composable
fun OverviewScreen(
    onNavigateToSettings: () -> Unit,
    viewModel: OverviewViewModel = hiltViewModel()
) {
    val cyclone by viewModel.cyclone.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(PukaarColors.BgVoid)
    ) {
        // Top Header
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                StatusDot(color = PukaarColors.AccentRed)
                Text(
                    text = "STORM INTELLIGENCE",
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 22.sp,
                    letterSpacing = 1.5.sp,
                    color = PukaarColors.TextPrimary
                )
            }

            IconButton(onClick = onNavigateToSettings) {
                Icon(
                    imageVector = Icons.Default.Settings,
                    contentDescription = "Settings",
                    tint = PukaarColors.TextSecondary
                )
            }
        }

        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Storm Details GlowCard
            item {
                GlowCard(
                    glowColor = PukaarColors.AccentRed,
                    pulse = true,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = cyclone?.name ?: "Super Cyclone Varuna",
                                fontFamily = RajdhaniFontFamily,
                                fontWeight = FontWeight.Bold,
                                fontSize = 26.sp,
                                color = PukaarColors.TextPrimary
                            )
                            RiskBadge(riskLevel = cyclone?.riskLevel ?: RiskLevel.EXTREME)
                        }

                        Text(
                            text = cyclone?.category ?: "Category 4 Very Severe Cyclonic Storm",
                            style = MaterialTheme.typography.bodySmall,
                            color = PukaarColors.TextSecondary
                        )

                        Spacer(modifier = Modifier.height(16.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            DataLabel(label = "R64 Hurricane", value = "${cyclone?.r64Km?.toInt() ?: 75}", unit = "km", valueColor = PukaarColors.AccentRed)
                            DataLabel(label = "R50 Severe", value = "${cyclone?.r50Km?.toInt() ?: 140}", unit = "km", valueColor = PukaarColors.AccentAmber)
                            DataLabel(label = "R34 Outer", value = "${cyclone?.r34Km?.toInt() ?: 240}", unit = "km", valueColor = PukaarColors.AccentYellow)
                        }
                    }
                }
            }

            item {
                GlowCard(
                    glowColor = PukaarColors.AccentCyan,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        Text(
                            text = "AI MODEL FORECAST CALIBRATION",
                            style = MaterialTheme.typography.labelSmall,
                            color = PukaarColors.AccentCyan
                        )

                        ConfidenceBar(label = "Landfall Spatial Probability", progress = 0.94f)
                        ConfidenceBar(label = "Wind Model Kinematic Calibration", progress = 0.91f)
                        ConfidenceBar(label = "Storm Surge Inundation Certainty", progress = 0.88f)
                    }
                }
            }

            item {
                Text(
                    text = "DISASTER TRAJECTORY WAYPOINTS",
                    style = MaterialTheme.typography.labelSmall,
                    color = PukaarColors.TextSecondary
                )
            }

            cyclone?.trajectory?.forEach { point ->
                item {
                    GlowCard(
                        glowColor = PukaarColors.BgElevated,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text(
                                    text = point.label,
                                    fontFamily = RajdhaniFontFamily,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 16.sp,
                                    color = PukaarColors.TextPrimary
                                )
                                Text(
                                    text = "${point.latitude}°N, ${point.longitude}°E",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = PukaarColors.TextSecondary
                                )
                            }

                            Text(
                                text = "${point.windKts.toInt()} kts",
                                fontFamily = RajdhaniFontFamily,
                                fontWeight = FontWeight.Bold,
                                fontSize = 20.sp,
                                color = PukaarColors.AccentRed
                            )
                        }
                    }
                }
            }

            item {
                Spacer(modifier = Modifier.height(16.dp))
            }
        }
    }
}
