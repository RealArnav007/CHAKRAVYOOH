package com.chakravyuh.android.ui.screens.sos

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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Emergency
import androidx.compose.material.icons.filled.LocalHospital
import androidx.compose.material.icons.filled.People
import androidx.compose.material.icons.filled.WaterDrop
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.chakravyuh.android.domain.model.ThreatLevel
import com.chakravyuh.android.ui.components.ChakravyuhTopBar
import com.chakravyuh.android.ui.components.PulsingBeacon
import com.chakravyuh.android.ui.theme.ChakravyuhBackground
import com.chakravyuh.android.ui.theme.ChakravyuhOutline
import com.chakravyuh.android.ui.theme.ChakravyuhPrimary
import com.chakravyuh.android.ui.theme.ChakravyuhSurface
import com.chakravyuh.android.ui.theme.SosRedGlow
import com.chakravyuh.android.ui.theme.ThreatExtreme
import com.chakravyuh.android.ui.theme.ThreatLow

@Composable
fun SosScreen(
    onNavigateToSettings: () -> Unit,
    viewModel: SosViewModel = hiltViewModel()
) {
    val activeSos by viewModel.activeSos.collectAsState()

    var emergencyType by remember { mutableStateOf("MEDICAL") }
    var victimCount by remember { mutableIntStateOf(1) }
    var notes by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(ChakravyuhBackground)
    ) {
        ChakravyuhTopBar(
            title = "Pukar SOS Distress",
            threatLevel = ThreatLevel.EXTREME,
            onSettingsClick = onNavigateToSettings
        )

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            if (activeSos != null) {
                // Active SOS Distress Beacon State
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Spacer(modifier = Modifier.height(24.dp))
                    PulsingBeacon(color = ThreatExtreme, size = 64.dp)
                    Spacer(modifier = Modifier.height(24.dp))

                    Text(
                        text = "DISTRESS BEACON ACTIVE",
                        style = MaterialTheme.typography.headlineMedium.copy(
                            fontWeight = FontWeight.Black,
                            letterSpacing = 2.sp
                        ),
                        color = ThreatExtreme
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = "SOS ID: ${activeSos!!.sosId}",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(12.dp))
                            .background(ChakravyuhSurface)
                            .border(1.dp, ThreatExtreme, RoundedCornerShape(12.dp))
                            .padding(16.dp)
                    ) {
                        Column {
                            Text(
                                text = "STATUS: ${activeSos!!.status.name}",
                                style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                                color = ThreatLow
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "Transmitting encrypted packets via offline Bluetooth Mesh to nearest NDRF command center.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }

                Button(
                    onClick = { viewModel.cancelEmergency(activeSos!!.sosId) },
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                    modifier = Modifier.fillMaxWidth().height(52.dp)
                ) {
                    Text(
                        text = "CANCEL DISTRESS SIGNAL",
                        color = MaterialTheme.colorScheme.onBackground,
                        style = MaterialTheme.typography.titleMedium
                    )
                }
            } else {
                // Emergency Trigger Form
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    Text(
                        text = "SELECT EMERGENCY CLASSIFICATION",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        val types = listOf(
                            Triple("MEDICAL", "Medical", Icons.Default.LocalHospital),
                            Triple("TRAPPED", "Trapped", Icons.Default.Warning),
                            Triple("FOOD_WATER", "Rations", Icons.Default.WaterDrop)
                        )

                        types.forEach { (key, label, icon) ->
                            val selected = emergencyType == key
                            Column(
                                modifier = Modifier
                                    .weight(1f)
                                    .clip(RoundedCornerShape(12.dp))
                                    .background(if (selected) ThreatExtreme.copy(alpha = 0.2f) else ChakravyuhSurface)
                                    .border(
                                        1.dp,
                                        if (selected) ThreatExtreme else ChakravyuhOutline,
                                        RoundedCornerShape(12.dp)
                                    )
                                    .clickable { emergencyType = key }
                                    .padding(12.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Icon(
                                    imageVector = icon,
                                    contentDescription = null,
                                    tint = if (selected) ThreatExtreme else MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(
                                    text = label,
                                    style = MaterialTheme.typography.labelSmall.copy(fontWeight = FontWeight.Bold),
                                    color = if (selected) Color.White else MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }

                    Text(
                        text = "VICTIM COUNT: $victimCount",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        listOf(1, 2, 5, 10).forEach { count ->
                            val selected = victimCount == count
                            Box(
                                modifier = Modifier
                                    .weight(1f)
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(if (selected) ChakravyuhPrimary.copy(alpha = 0.2f) else ChakravyuhSurface)
                                    .border(1.dp, if (selected) ChakravyuhPrimary else ChakravyuhOutline, RoundedCornerShape(8.dp))
                                    .clickable { victimCount = count }
                                    .padding(vertical = 10.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = "$count+",
                                    color = if (selected) ChakravyuhPrimary else MaterialTheme.colorScheme.onSurfaceVariant,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }
                    }

                    OutlinedTextField(
                        value = notes,
                        onValueChange = { notes = it },
                        label = { Text("Medical / Critical Notes (e.g. Oxygen needed)") },
                        modifier = Modifier.fillMaxWidth(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = ChakravyuhPrimary,
                            unfocusedBorderColor = ChakravyuhOutline,
                            focusedTextColor = MaterialTheme.colorScheme.onBackground,
                            unfocusedTextColor = MaterialTheme.colorScheme.onBackground
                        ),
                        maxLines = 3
                    )
                }

                // High Voltage SOS Trigger Button
                Button(
                    onClick = {
                        viewModel.triggerEmergencySos(
                            emergencyType = emergencyType,
                            victimCount = victimCount,
                            notes = notes
                        )
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = ThreatExtreme),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(60.dp)
                        .clip(RoundedCornerShape(16.dp))
                ) {
                    Icon(imageVector = Icons.Default.Emergency, contentDescription = null)
                    Spacer(modifier = Modifier.size(8.dp))
                    Text(
                        text = "TRANSMIT PUKAR SOS",
                        style = MaterialTheme.typography.titleMedium.copy(
                            fontWeight = FontWeight.Black,
                            letterSpacing = 1.sp
                        )
                    )
                }
            }
        }
    }
}
