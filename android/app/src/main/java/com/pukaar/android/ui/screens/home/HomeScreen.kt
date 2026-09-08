package com.pukaar.android.ui.screens.home

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CrisisAlert
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
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
fun HomeScreen(
    onNavigateToAlerts: () -> Unit,
    onNavigateToSos: () -> Unit,
    onNavigateToSettings: () -> Unit,
    viewModel: HomeViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val cyclone = state.cyclone

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
                    text = "PUKAAR TACTICAL",
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 22.sp,
                    letterSpacing = 1.5.sp,
                    color = PukaarColors.TextPrimary
                )
            }

            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                RiskBadge(riskLevel = state.highestRisk)
                IconButton(onClick = onNavigateToSettings) {
                    Icon(
                        imageVector = Icons.Default.Settings,
                        contentDescription = "Settings",
                        tint = PukaarColors.TextSecondary
                    )
                }
            }
        }

        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // SOS Emergency Banner
            item {
                Button(
                    onClick = onNavigateToSos,
                    colors = ButtonDefaults.buttonColors(containerColor = PukaarColors.AccentRed),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp)
                ) {
                    Icon(imageVector = Icons.Default.CrisisAlert, contentDescription = null, tint = Color.White)
                    Spacer(modifier = Modifier.padding(horizontal = 4.dp))
                    Text(
                        text = "EMERGENCY SOS DISTRESS",
                        fontFamily = RajdhaniFontFamily,
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp,
                        letterSpacing = 1.sp,
                        color = Color.White
                    )
                }
            }

            // Cyclone Intelligence Card
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
                                fontSize = 24.sp,
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

                        // Metric Grids using DataLabel
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            DataLabel(
                                label = "Sustained Wind",
                                value = "${cyclone?.currentWindSpeedKts?.toInt() ?: 125}",
                                unit = "kts",
                                valueColor = PukaarColors.AccentRed
                            )
                            DataLabel(
                                label = "Core Pressure",
                                value = "${cyclone?.centralPressureHpa?.toInt() ?: 932}",
                                unit = "hPa",
                                valueColor = PukaarColors.AccentAmber
                            )
                            DataLabel(
                                label = "Landfall ETA",
                                value = "5.5",
                                unit = "hrs",
                                valueColor = PukaarColors.AccentCyan
                            )
                        }

                        Spacer(modifier = Modifier.height(16.dp))

                        ConfidenceBar(
                            label = "AI Landfall Trajectory Calibration",
                            progress = (cyclone?.landfallProbability?.toFloat() ?: 0.94f)
                        )
                    }
                }
            }

            // Mesh Network Health
            item {
                GlowCard(
                    glowColor = PukaarColors.AccentCyan,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(
                                text = "BLUETOOTH LE OFFLINE MESH",
                                style = MaterialTheme.typography.labelSmall,
                                color = PukaarColors.AccentCyan
                            )
                            Spacer(modifier = Modifier.height(2.dp))
                            Text(
                                text = "${state.peers.size} Active Relay Nodes in Proximity",
                                fontFamily = RajdhaniFontFamily,
                                fontWeight = FontWeight.Bold,
                                fontSize = 18.sp,
                                color = PukaarColors.TextPrimary
                            )
                            Text(
                                text = "Decentralized mesh packet propagation active",
                                style = MaterialTheme.typography.bodySmall,
                                color = PukaarColors.TextSecondary
                            )
                        }

                        StatusDot(color = PukaarColors.AccentGreen, label = "RELAY")
                    }
                }
            }

            // Active Alerts Section
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "ACTIVE EVACUATION NOTICES",
                        style = MaterialTheme.typography.labelSmall,
                        color = PukaarColors.TextSecondary
                    )
                    Text(
                        text = "VIEW ALL (${state.alerts.size})",
                        style = MaterialTheme.typography.labelSmall.copy(fontWeight = FontWeight.Bold),
                        color = PukaarColors.AccentCyan,
                        modifier = Modifier.clickable { onNavigateToAlerts() }
                    )
                }
            }

            items(state.alerts.take(2)) { alert ->
                GlowCard(
                    glowColor = PukaarColors.forRiskLevel(alert.riskLevel),
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onNavigateToAlerts() }
                ) {
                    Column {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = alert.zone.uppercase(),
                                style = MaterialTheme.typography.labelSmall,
                                color = PukaarColors.TextSecondary
                            )
                            RiskBadge(riskLevel = alert.riskLevel)
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = alert.title,
                            fontFamily = RajdhaniFontFamily,
                            fontWeight = FontWeight.Bold,
                            fontSize = 18.sp,
                            color = PukaarColors.TextPrimary
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = alert.actionAdvice,
                            style = MaterialTheme.typography.bodySmall,
                            color = PukaarColors.forRiskLevel(alert.riskLevel)
                        )
                    }
                }
            }

            item {
                Spacer(modifier = Modifier.height(16.dp))
            }
        }
    }
}
