package com.chakravyuh.android.ui.screens.mesh

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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BluetoothSearching
import androidx.compose.material.icons.filled.Hub
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.chakravyuh.android.domain.model.ThreatLevel
import com.chakravyuh.android.ui.components.ChakravyuhTopBar
import com.chakravyuh.android.ui.theme.ChakravyuhBackground
import com.chakravyuh.android.ui.theme.ChakravyuhOutline
import com.chakravyuh.android.ui.theme.ChakravyuhPrimary
import com.chakravyuh.android.ui.theme.ChakravyuhSurface
import com.chakravyuh.android.ui.theme.ThreatLow

@Composable
fun MeshScreen(
    onNavigateToSettings: () -> Unit,
    viewModel: MeshViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsState()
    var messageInput by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(ChakravyuhBackground)
    ) {
        ChakravyuhTopBar(
            title = "Decentralized Mesh",
            threatLevel = ThreatLevel.LOW,
            onSettingsClick = onNavigateToSettings
        )

        LazyColumn(
            modifier = Modifier
                .weight(1f)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            item {
                Spacer(modifier = Modifier.height(4.dp))
                // Mesh Topology Status Banner
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(12.dp))
                        .background(ChakravyuhSurface)
                        .border(1.dp, ChakravyuhPrimary.copy(alpha = 0.5f), RoundedCornerShape(12.dp))
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                modifier = Modifier
                                    .size(8.dp)
                                    .clip(CircleShape)
                                    .background(ThreatLow)
                            )
                            Spacer(modifier = Modifier.size(6.dp))
                            Text(
                                text = "P2P RELAY ACTIVE",
                                style = MaterialTheme.typography.labelSmall,
                                color = ThreatLow
                            )
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "${state.discoveredNodes.size} Peer Nodes Connected",
                            style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                            color = MaterialTheme.colorScheme.onBackground
                        )
                    }

                    Icon(
                        imageVector = Icons.Default.BluetoothSearching,
                        contentDescription = null,
                        tint = ChakravyuhPrimary,
                        modifier = Modifier.size(28.dp)
                    )
                }
            }

            item {
                Text(
                    text = "DISCOVERED MESH RELAY NODES",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            items(state.discoveredNodes) { node ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(10.dp))
                        .background(ChakravyuhSurface)
                        .border(1.dp, ChakravyuhOutline, RoundedCornerShape(10.dp))
                        .padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = node.deviceName,
                            style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.SemiBold),
                            color = MaterialTheme.colorScheme.onBackground
                        )
                        Text(
                            text = "Node ID: ${node.nodeId} • ${node.hopCount} Hops",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }

                    Text(
                        text = "${node.signalStrengthRssi} dBm",
                        style = MaterialTheme.typography.labelSmall.copy(fontWeight = FontWeight.Bold),
                        color = ThreatLow
                    )
                }
            }

            item {
                Text(
                    text = "LOCAL MESH PACKETS",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            items(state.messages) { message ->
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(ChakravyuhSurface)
                        .padding(10.dp)
                ) {
                    Column {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                text = "From: ${message.senderNodeId}",
                                style = MaterialTheme.typography.labelSmall,
                                color = ChakravyuhPrimary
                            )
                            Text(
                                text = if (message.isDelivered) "Delivered" else "Relaying",
                                style = MaterialTheme.typography.labelSmall,
                                color = ThreatLow
                            )
                        }
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = message.payload,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onBackground
                        )
                    }
                }
            }
        }

        // Broadcast Message Bar
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(ChakravyuhSurface)
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedTextField(
                value = messageInput,
                onValueChange = { messageInput = it },
                placeholder = { Text("Broadcast encrypted mesh packet...") },
                modifier = Modifier.weight(1f),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = ChakravyuhPrimary,
                    unfocusedBorderColor = ChakravyuhOutline,
                    focusedTextColor = MaterialTheme.colorScheme.onBackground,
                    unfocusedTextColor = MaterialTheme.colorScheme.onBackground
                ),
                maxLines = 1
            )
            Spacer(modifier = Modifier.size(8.dp))
            IconButton(
                onClick = {
                    if (messageInput.isNotBlank()) {
                        viewModel.sendBroadcast(messageInput)
                        messageInput = ""
                    }
                },
                modifier = Modifier
                    .clip(CircleShape)
                    .background(ChakravyuhPrimary)
            ) {
                Icon(
                    imageVector = Icons.Default.Send,
                    contentDescription = "Send",
                    tint = Color.White
                )
            }
        }
    }
}
