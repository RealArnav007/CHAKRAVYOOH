package com.pukaar.android.ui.screens.onboarding

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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
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
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily

@Composable
fun OnboardingScreen(
    onFinish: () -> Unit,
    viewModel: OnboardingViewModel = hiltViewModel()
) {
    var name by remember { mutableStateOf("") }
    var phone by remember { mutableStateOf("") }
    var bloodGroup by remember { mutableStateOf("O+") }
    var meshRelay by remember { mutableStateOf(true) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(PukaarColors.BgVoid)
            .padding(24.dp),
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        Column {
            Spacer(modifier = Modifier.height(24.dp))
            Text(
                text = "INITIALIZE NODE",
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 32.sp,
                letterSpacing = 2.sp,
                color = PukaarColors.TextPrimary
            )
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = "Pukaar operates over decentralized Bluetooth LE mesh when cellular towers collapse. Configure your emergency responder identity.",
                style = MaterialTheme.typography.bodyMedium,
                color = PukaarColors.TextSecondary
            )

            Spacer(modifier = Modifier.height(28.dp))

            GlowCard(
                glowColor = PukaarColors.AccentCyan,
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
                    OutlinedTextField(
                        value = name,
                        onValueChange = { name = it },
                        label = { Text("Your Name / Call Sign") },
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
                        onValueChange = { phone = it },
                        label = { Text("Emergency Contact Phone") },
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
                        onValueChange = { bloodGroup = it },
                        label = { Text("Blood Group (e.g. O+, B-, AB+)") },
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

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(10.dp))
                    .background(PukaarColors.BgSurface)
                    .border(1.dp, PukaarColors.BgElevated, RoundedCornerShape(10.dp))
                    .padding(14.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "Enable Offline Mesh Relay",
                        style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.SemiBold),
                        color = PukaarColors.TextPrimary
                    )
                    Text(
                        text = "Relays encrypted distress packets from trapped citizens nearby.",
                        style = MaterialTheme.typography.bodySmall,
                        color = PukaarColors.TextSecondary
                    )
                }
                Switch(
                    checked = meshRelay,
                    onCheckedChange = { meshRelay = it },
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = PukaarColors.AccentCyan,
                        checkedTrackColor = PukaarColors.AccentCyan.copy(alpha = 0.3f)
                    )
                )
            }
        }

        Button(
            onClick = {
                viewModel.completeOnboarding(
                    name = name.ifBlank { "Citizen Responder" },
                    phone = phone.ifBlank { "+91-112" },
                    bloodGroup = bloodGroup.ifBlank { "O+" },
                    meshRelay = meshRelay
                )
                onFinish()
            },
            colors = ButtonDefaults.buttonColors(containerColor = PukaarColors.AccentCyan),
            modifier = Modifier
                .fillMaxWidth()
                .height(52.dp)
                .clip(RoundedCornerShape(10.dp))
        ) {
            Text(
                text = "ENTER TACTICAL DASHBOARD",
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                color = PukaarColors.BgVoid
            )
        }
    }
}
