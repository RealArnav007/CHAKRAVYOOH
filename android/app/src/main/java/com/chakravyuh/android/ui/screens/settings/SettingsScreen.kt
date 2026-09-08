package com.chakravyuh.android.ui.screens.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.chakravyuh.android.domain.model.ThreatLevel
import com.chakravyuh.android.ui.components.ChakravyuhTopBar
import com.chakravyuh.android.ui.theme.ChakravyuhBackground
import com.chakravyuh.android.ui.theme.ChakravyuhOutline
import com.chakravyuh.android.ui.theme.ChakravyuhPrimary
import com.chakravyuh.android.ui.theme.ChakravyuhSurface

@Composable
fun SettingsScreen(
    onNavigateBack: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel()
) {
    val settings by viewModel.settings.collectAsState()

    var userName by remember(settings.userName) { mutableStateOf(settings.userName) }
    var emergencyContact by remember(settings.emergencyContactPhone) { mutableStateOf(settings.emergencyContactPhone) }
    var bloodGroup by remember(settings.bloodGroup) { mutableStateOf(settings.bloodGroup) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(ChakravyuhBackground)
    ) {
        ChakravyuhTopBar(
            title = "Configuration",
            threatLevel = ThreatLevel.NORMAL,
            onSettingsClick = onNavigateBack
        )

        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item {
                Text(
                    text = "RESPONDER PROFILE",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))

                OutlinedTextField(
                    value = userName,
                    onValueChange = {
                        userName = it
                        viewModel.updateSettings(settings.copy(userName = it))
                    },
                    label = { Text("Citizen / Responder Name") },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = ChakravyuhPrimary,
                        unfocusedBorderColor = ChakravyuhOutline,
                        focusedTextColor = MaterialTheme.colorScheme.onBackground,
                        unfocusedTextColor = MaterialTheme.colorScheme.onBackground
                    )
                )

                Spacer(modifier = Modifier.height(10.dp))

                OutlinedTextField(
                    value = emergencyContact,
                    onValueChange = {
                        emergencyContact = it
                        viewModel.updateSettings(settings.copy(emergencyContactPhone = it))
                    },
                    label = { Text("Primary Emergency Phone") },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = ChakravyuhPrimary,
                        unfocusedBorderColor = ChakravyuhOutline,
                        focusedTextColor = MaterialTheme.colorScheme.onBackground,
                        unfocusedTextColor = MaterialTheme.colorScheme.onBackground
                    )
                )

                Spacer(modifier = Modifier.height(10.dp))

                OutlinedTextField(
                    value = bloodGroup,
                    onValueChange = {
                        bloodGroup = it
                        viewModel.updateSettings(settings.copy(bloodGroup = it))
                    },
                    label = { Text("Blood Group") },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = ChakravyuhPrimary,
                        unfocusedBorderColor = ChakravyuhOutline,
                        focusedTextColor = MaterialTheme.colorScheme.onBackground,
                        unfocusedTextColor = MaterialTheme.colorScheme.onBackground
                    )
                )
            }

            item {
                Text(
                    text = "OFFLINE MESH & RESILIENCE PREFERENCES",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))

                // Toggle 1: Background Mesh Relay
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(10.dp))
                        .background(ChakravyuhSurface)
                        .border(1.dp, ChakravyuhOutline, RoundedCornerShape(10.dp))
                        .padding(14.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "Decentralized Mesh Relay",
                            style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.SemiBold),
                            color = MaterialTheme.colorScheme.onBackground
                        )
                        Text(
                            text = "Forward distress & warning packets for nearby citizens even when cellular towers fall.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    Switch(
                        checked = settings.isMeshRelayEnabled,
                        onCheckedChange = { viewModel.toggleMeshRelay(it) },
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = ChakravyuhPrimary,
                            checkedTrackColor = ChakravyuhPrimary.copy(alpha = 0.3f)
                        )
                    )
                }

                Spacer(modifier = Modifier.height(10.dp))

                // Toggle 2: Critical Audio Siren
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(10.dp))
                        .background(ChakravyuhSurface)
                        .border(1.dp, ChakravyuhOutline, RoundedCornerShape(10.dp))
                        .padding(14.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "Critical Emergency Siren",
                            style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.SemiBold),
                            color = MaterialTheme.colorScheme.onBackground
                        )
                        Text(
                            text = "Override DND during RED / Extreme storm surge evacuation warnings.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    Switch(
                        checked = settings.isCriticalAudioAlertEnabled,
                        onCheckedChange = {
                            viewModel.updateSettings(settings.copy(isCriticalAudioAlertEnabled = it))
                        },
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = ChakravyuhPrimary,
                            checkedTrackColor = ChakravyuhPrimary.copy(alpha = 0.3f)
                        )
                    )
                }
            }

            item {
                Spacer(modifier = Modifier.height(24.dp))
            }
        }
    }
}
