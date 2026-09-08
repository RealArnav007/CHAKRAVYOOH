package com.chakravyuh.android.ui.screens.overview

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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CrisisAlert
import androidx.compose.material.icons.filled.Speed
import androidx.compose.material.icons.filled.Waves
import androidx.compose.material.icons.filled.WindPower
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.chakravyuh.android.domain.model.ThreatLevel
import com.chakravyuh.android.ui.components.ChakravyuhTopBar
import com.chakravyuh.android.ui.components.StatusCard
import com.chakravyuh.android.ui.components.ThreatBadge
import com.chakravyuh.android.ui.theme.ChakravyuhBackground
import com.chakravyuh.android.ui.theme.ChakravyuhOutline
import com.chakravyuh.android.ui.theme.ChakravyuhPrimary
import com.chakravyuh.android.ui.theme.ChakravyuhSurface
import com.chakravyuh.android.ui.theme.ThreatExtreme
import com.chakravyuh.android.ui.theme.ThreatHigh
import com.chakravyuh.android.ui.theme.ThreatModerate

@Composable
fun OverviewScreen(
    onNavigateToSettings: () -> Unit,
    viewModel: OverviewViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsState()
    val cyclone = state.cyclone

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(ChakravyuhBackground)
    ) {
        ChakravyuhTopBar(
            title = "Storm Intelligence",
            threatLevel = cyclone?.threatLevel ?: ThreatExtreme,
            onSettingsClick = onNavigateToSettings
        )

        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item {
                Spacer(modifier = Modifier.height(4.dp))
                // Storm Banner Card
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(12.dp))
                        .background(ChakravyuhSurface)
                        .border(1.dp, ThreatExtreme.copy(alpha = 0.5f), RoundedCornerShape(12.dp))
                        .padding(16.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = cyclone?.category ?: "Super Cyclonic Storm",
                            style = MaterialTheme.typography.labelSmall,
                            color = ThreatExtreme
                        )
                        ThreatBadge(threatLevel = cyclone?.threatLevel ?: ThreatExtreme)
                    }

                    Spacer(modifier = Modifier.height(6.dp))

                    Text(
                        text = cyclone?.name ?: "Super Cyclone Varuna",
                        style = MaterialTheme.typography.headlineMedium.copy(fontWeight = FontWeight.Bold),
                        color = MaterialTheme.colorScheme.onBackground
                    )

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        text = "Landfall expected near Puri-Paradip coastline. Maximum sustained winds 125 knots with severe surge flooding in coastal lowlands.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            item {
                Text(
                    text = "CRITICAL RADII METRICS",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    StatusCard(
                        title = "R64 Hurricane",
                        value = "${cyclone?.r64RadiusKm?.toInt() ?: 75} km",
                        subtitle = ">64 kts core",
                        icon = Icons.Default.WindPower,
                        accentColor = ThreatExtreme,
                        modifier = Modifier.weight(1f)
                    )
                    StatusCard(
                        title = "R50 Destructive",
                        value = "${cyclone?.r50RadiusKm?.toInt() ?: 140} km",
                        subtitle = ">50 kts reach",
                        icon = Icons.Default.CrisisAlert,
                        accentColor = ThreatHigh,
                        modifier = Modifier.weight(1f)
                    )
                }
            }

            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    StatusCard(
                        title = "R34 Gale Zone",
                        value = "${cyclone?.r34RadiusKm?.toInt() ?: 240} km",
                        subtitle = ">34 kts outer",
                        icon = Icons.Default.Waves,
                        accentColor = ThreatModerate,
                        modifier = Modifier.weight(1f)
                    )
                    StatusCard(
                        title = "Central Pressure",
                        value = "${cyclone?.currentPressureHpa?.toInt() ?: 932} hPa",
                        subtitle = "Deep depression",
                        icon = Icons.Default.Speed,
                        accentColor = ChakravyuhPrimary,
                        modifier = Modifier.weight(1f)
                    )
                }
            }

            item {
                Text(
                    text = "FORECAST TRACK TRAJECTORY",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))

                cyclone?.forecastTrack?.forEach { point ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp)
                            .clip(RoundedCornerShape(8.dp))
                            .background(ChakravyuhSurface)
                            .border(1.dp, ChakravyuhOutline, RoundedCornerShape(8.dp))
                            .padding(12.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(
                                text = "${point.latitude}°N, ${point.longitude}°E",
                                style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.SemiBold),
                                color = MaterialTheme.colorScheme.onBackground
                            )
                            Text(
                                text = point.intensityCategory,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }

                        Text(
                            text = "${point.windSpeedKts.toInt()} kts",
                            style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                            color = ThreatExtreme
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
