package com.chakravyuh.android.ui.screens.home

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
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Air
import androidx.compose.material.icons.filled.Compress
import androidx.compose.material.icons.filled.Hub
import androidx.compose.material.icons.filled.Timer
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.chakravyuh.android.domain.model.ThreatLevel
import com.chakravyuh.android.ui.components.AlertItemCard
import com.chakravyuh.android.ui.components.ChakravyuhTopBar
import com.chakravyuh.android.ui.components.StatusCard
import com.chakravyuh.android.ui.theme.ChakravyuhBackground
import com.chakravyuh.android.ui.theme.ThreatExtreme
import com.chakravyuh.android.ui.theme.ThreatHigh

@Composable
fun HomeScreen(
    onNavigateToAlerts: () -> Unit,
    onNavigateToSos: () -> Unit,
    onNavigateToSettings: () -> Unit,
    viewModel: HomeViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(ChakravyuhBackground)
    ) {
        ChakravyuhTopBar(
            title = "Tactical Command",
            threatLevel = state.currentThreatLevel,
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
                // Quick SOS Button
                Button(
                    onClick = onNavigateToSos,
                    colors = ButtonDefaults.buttonColors(containerColor = ThreatExtreme),
                    modifier = Modifier.fillMaxWidth().height(52.dp)
                ) {
                    Text(
                        text = "EMERGENCY SOS (PUKAR DISPATCH)",
                        style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold)
                    )
                }
            }

            item {
                Text(
                    text = "CYCLONE TELEMETRY",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    StatusCard(
                        title = "Wind Speed",
                        value = "${state.cyclone?.maxSustainedWindKts?.toInt() ?: 125} kts",
                        subtitle = "Gusts to 145 kts",
                        icon = Icons.Default.Air,
                        accentColor = ThreatExtreme,
                        modifier = Modifier.weight(1f)
                    )
                    StatusCard(
                        title = "Pressure",
                        value = "${state.cyclone?.currentPressureHpa?.toInt() ?: 932} hPa",
                        subtitle = "Rapid drop",
                        icon = Icons.Default.Compress,
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
                        title = "Landfall ETA",
                        value = "5h 45m",
                        subtitle = "Prob: ${(state.cyclone?.landfallProbability?.times(100))?.toInt() ?: 94}%",
                        icon = Icons.Default.Timer,
                        accentColor = ThreatExtreme,
                        modifier = Modifier.weight(1f)
                    )
                    StatusCard(
                        title = "Mesh Peers",
                        value = "${state.meshNodes.size} Active",
                        subtitle = "Decentralized relay",
                        icon = Icons.Default.Hub,
                        accentColor = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.weight(1f)
                    )
                }
            }

            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = "ACTIVE EVACUATION ALERTS",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        text = "${state.alerts.size} Active",
                        style = MaterialTheme.typography.labelSmall,
                        color = ThreatExtreme
                    )
                }
            }

            items(state.alerts) { alert ->
                AlertItemCard(
                    alert = alert,
                    onBroadcastMesh = { onNavigateToAlerts() },
                    onClick = onNavigateToAlerts
                )
            }

            item {
                Spacer(modifier = Modifier.height(16.dp))
            }
        }
    }
}
