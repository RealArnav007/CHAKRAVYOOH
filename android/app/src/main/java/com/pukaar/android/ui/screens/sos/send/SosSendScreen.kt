package com.pukaar.android.ui.screens.sos.send

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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CrisisAlert
import androidx.compose.material.icons.filled.LocalHospital
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.filled.WaterDrop
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
import com.pukaar.android.ui.components.ConfidenceBar
import com.pukaar.android.ui.components.GlowCard
import com.pukaar.android.ui.components.StatusDot
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily

@Composable
fun SosSendScreen(
    viewModel: SosSendViewModel = hiltViewModel()
) {
    val activeSos by viewModel.activeSos.collectAsState()

    var emergencyType by remember { mutableStateOf("MEDICAL") }
    var victimCount by remember { mutableIntStateOf(1) }
    var notes by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        if (activeSos != null) {
            // Active SOS Distress Beacon View
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Spacer(modifier = Modifier.height(16.dp))
                StatusDot(color = PukaarColors.AccentRed)
                Spacer(modifier = Modifier.height(12.dp))

                Text(
                    text = "DISTRESS BEACON BROADCASTING",
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 26.sp,
                    color = PukaarColors.AccentRed
                )

                Text(
                    text = "ID: ${activeSos!!.id}",
                    style = MaterialTheme.typography.labelSmall,
                    color = PukaarColors.TextSecondary
                )

                Spacer(modifier = Modifier.height(20.dp))

                GlowCard(
                    glowColor = PukaarColors.AccentRed,
                    pulse = true,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(
                            text = "STATUS: ${activeSos!!.status.name}",
                            fontFamily = RajdhaniFontFamily,
                            fontWeight = FontWeight.Bold,
                            fontSize = 18.sp,
                            color = PukaarColors.AccentGreen
                        )
                        Text(
                            text = "Transmitting encrypted ECDSA packets to nearby Bluetooth LE relay nodes. No cellular uplink required.",
                            style = MaterialTheme.typography.bodySmall,
                            color = PukaarColors.TextSecondary
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        ConfidenceBar(label = "Mesh Relay Propagation", progress = 0.85f, indicatorColor = PukaarColors.AccentRed)
                    }
                }
            }

            Button(
                onClick = { viewModel.cancelSos(activeSos!!.id) },
                colors = ButtonDefaults.buttonColors(containerColor = PukaarColors.BgElevated),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp)
            ) {
                Text(
                    text = "CANCEL EMERGENCY DISTRESS",
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp,
                    color = PukaarColors.TextPrimary
                )
            }
        } else {
            // Form to Trigger SOS
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Text(
                    text = "SELECT EMERGENCY CLASSIFICATION",
                    style = MaterialTheme.typography.labelSmall,
                    color = PukaarColors.TextSecondary
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    val types = listOf(
                        Triple("MEDICAL", "Medical", Icons.Default.LocalHospital),
                        Triple("TRAPPED", "Trapped", Icons.Default.Warning),
                        Triple("RATIONS", "Rations", Icons.Default.WaterDrop)
                    )

                    types.forEach { (key, label, icon) ->
                        val selected = emergencyType == key
                        Column(
                            modifier = Modifier
                                .weight(1f)
                                .clip(RoundedCornerShape(10.dp))
                                .background(if (selected) PukaarColors.AccentRed.copy(alpha = 0.2f) else PukaarColors.BgSurface)
                                .border(
                                    1.dp,
                                    if (selected) PukaarColors.AccentRed else PukaarColors.BgElevated,
                                    RoundedCornerShape(10.dp)
                                )
                                .clickable { emergencyType = key }
                                .padding(12.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Icon(
                                imageVector = icon,
                                contentDescription = null,
                                tint = if (selected) PukaarColors.AccentRed else PukaarColors.TextSecondary
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = label,
                                style = MaterialTheme.typography.labelSmall,
                                color = if (selected) Color.White else PukaarColors.TextSecondary
                            )
                        }
                    }
                }

                Text(
                    text = "NUMBER OF PERSONS: $victimCount",
                    style = MaterialTheme.typography.labelSmall,
                    color = PukaarColors.TextSecondary
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    listOf(1, 2, 5, 10).forEach { count ->
                        val selected = victimCount == count
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .clip(RoundedCornerShape(8.dp))
                                .background(if (selected) PukaarColors.AccentCyan.copy(alpha = 0.2f) else PukaarColors.BgSurface)
                                .border(1.dp, if (selected) PukaarColors.AccentCyan else PukaarColors.BgElevated, RoundedCornerShape(8.dp))
                            .clickable { victimCount = count }
                            .padding(vertical = 10.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "$count+",
                                fontFamily = RajdhaniFontFamily,
                                fontWeight = FontWeight.Bold,
                                color = if (selected) PukaarColors.AccentCyan else PukaarColors.TextSecondary
                            )
                        }
                    }
                }

                OutlinedTextField(
                    value = notes,
                    onValueChange = { notes = it },
                    label = { Text("Critical Notes (e.g. Oxygen needed, Child present)") },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = PukaarColors.AccentCyan,
                        unfocusedBorderColor = PukaarColors.BgElevated,
                        focusedTextColor = PukaarColors.TextPrimary,
                        unfocusedTextColor = PukaarColors.TextPrimary
                    ),
                    maxLines = 3
                )
            }

            Button(
                onClick = {
                    viewModel.sendEmergencySos(
                        emergencyType = emergencyType,
                        victimCount = victimCount,
                        notes = notes
                    )
                },
                colors = ButtonDefaults.buttonColors(containerColor = PukaarColors.AccentRed),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(58.dp)
                    .clip(RoundedCornerShape(12.dp))
            ) {
                Icon(imageVector = Icons.Default.CrisisAlert, contentDescription = null, tint = Color.White)
                Spacer(modifier = Modifier.size(8.dp))
                Text(
                    text = "TRANSMIT PUKAR SOS",
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp,
                    letterSpacing = 1.sp,
                    color = Color.White
                )
            }
        }
    }
}
