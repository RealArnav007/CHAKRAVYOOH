package com.pukaar.android.ui.screens.settings

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
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
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
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pukaar.android.ui.components.GlowCard
import com.pukaar.android.ui.components.StatusDot
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily

@Composable
fun SettingsScreen(
    onNavigateBack: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel()
) {
    val profile by viewModel.profile.collectAsState()

    var name by remember(profile.name) { mutableStateOf(profile.name) }
    var phone by remember(profile.phone) { mutableStateOf(profile.phone) }
    var bloodGroup by remember(profile.bloodGroup) { mutableStateOf(profile.bloodGroup) }

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
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = onNavigateBack) {
                Icon(
                    imageVector = Icons.Default.ArrowBack,
                    contentDescription = "Back",
                    tint = PukaarColors.TextPrimary
                )
            }
            Spacer(modifier = Modifier.padding(horizontal = 4.dp))
            StatusDot(color = PukaarColors.AccentCyan)
            Text(
                text = "CONFIGURATION",
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 22.sp,
                letterSpacing = 1.5.sp,
                color = PukaarColors.TextPrimary
            )
        }

        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item {
                GlowCard(
                    glowColor = PukaarColors.AccentCyan,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        Text(
                            text = "RESPONDER PROFILE",
                            style = MaterialTheme.typography.labelSmall,
                            color = PukaarColors.AccentCyan
                        )

                        OutlinedTextField(
                            value = name,
                            onValueChange = {
                                name = it
                                viewModel.updateProfile(profile.copy(name = it))
                            },
                            label = { Text("Responder Name") },
                            modifier = Modifier.fillMaxWidth(),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = PukaarColors.AccentCyan,
                                unfocusedBorderColor = PukaarColors.BgElevated,
                                focusedTextColor = PukaarColors.TextPrimary,
                                unfocusedTextColor = PukaarColors.TextPrimary
                            )
                        )

                        OutlinedTextField(
                            value = phone,
                            onValueChange = {
                                phone = it
                                viewModel.updateProfile(profile.copy(phone = it))
                            },
                            label = { Text("Emergency Contact") },
                            modifier = Modifier.fillMaxWidth(),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = PukaarColors.AccentCyan,
                                unfocusedBorderColor = PukaarColors.BgElevated,
                                focusedTextColor = PukaarColors.TextPrimary,
                                unfocusedTextColor = PukaarColors.TextPrimary
                            )
                        )

                        OutlinedTextField(
                            value = bloodGroup,
                            onValueChange = {
                                bloodGroup = it
                                viewModel.updateProfile(profile.copy(bloodGroup = it))
                            },
                            label = { Text("Blood Group") },
                            modifier = Modifier.fillMaxWidth(),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = PukaarColors.AccentCyan,
                                unfocusedBorderColor = PukaarColors.BgElevated,
                                focusedTextColor = PukaarColors.TextPrimary,
                                unfocusedTextColor = PukaarColors.TextPrimary
                            )
                        )
                    }
                }
            }

            item {
                GlowCard(
                    glowColor = PukaarColors.AccentGreen,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        Text(
                            text = "DECENTRALIZED RESILIENCE CONTROLS",
                            style = MaterialTheme.typography.labelSmall,
                            color = PukaarColors.AccentGreen
                        )

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = "Bluetooth LE Mesh Relay",
                                    fontFamily = RajdhaniFontFamily,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 16.sp,
                                    color = PukaarColors.TextPrimary
                                )
                                Text(
                                    text = "Forward distress packets for citizens during blackouts.",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = PukaarColors.TextSecondary
                                )
                            }
                            Switch(
                                checked = profile.isMeshRelayEnabled,
                                onCheckedChange = { viewModel.toggleMeshRelay(it) },
                                colors = SwitchDefaults.colors(
                                    checkedThumbColor = PukaarColors.AccentGreen,
                                    checkedTrackColor = PukaarColors.AccentGreen.copy(alpha = 0.3f)
                                )
                            )
                        }

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = "Emergency Audio Siren Override",
                                    fontFamily = RajdhaniFontFamily,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 16.sp,
                                    color = PukaarColors.TextPrimary
                                )
                                Text(
                                    text = "Sound critical evacuation alarms even when device is on DND.",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = PukaarColors.TextSecondary
                                )
                            }
                            Switch(
                                checked = profile.criticalSirenEnabled,
                                onCheckedChange = {
                                    viewModel.updateProfile(profile.copy(criticalSirenEnabled = it))
                                },
                                colors = SwitchDefaults.colors(
                                    checkedThumbColor = PukaarColors.AccentCyan,
                                    checkedTrackColor = PukaarColors.AccentCyan.copy(alpha = 0.3f)
                                )
                            )
                        }
                    }
                }
            }

            // Demo Mode Section
            item {
                GlowCard(
                    glowColor = PukaarColors.AccentAmber,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        Text(
                            text = "DEMO MODE",
                            fontFamily = RajdhaniFontFamily,
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp,
                            color = PukaarColors.AccentAmber
                        )

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = "Hackathon Demo Data",
                                    fontFamily = RajdhaniFontFamily,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 16.sp,
                                    color = PukaarColors.TextPrimary
                                )
                                Text(
                                    text = "Uses simulated cyclone data for presentation",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = PukaarColors.TextSecondary
                                )
                            }
                            Switch(
                                checked = profile.demoMode,
                                onCheckedChange = { viewModel.toggleDemoMode(it) },
                                colors = SwitchDefaults.colors(
                                    checkedThumbColor = PukaarColors.AccentAmber,
                                    checkedTrackColor = PukaarColors.AccentAmber.copy(alpha = 0.3f)
                                )
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
