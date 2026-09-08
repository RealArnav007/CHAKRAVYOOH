package com.pukaar.android.ui.screens.sos.inbox

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
import com.pukaar.android.ui.components.GlowCard
import com.pukaar.android.ui.components.StatusDot
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily

@Composable
fun SosInboxScreen(
    viewModel: SosInboxViewModel = hiltViewModel()
) {
    val messages by viewModel.inbox.collectAsState()

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            Text(
                text = "${messages.size} MESH RELAYED DISTRESS SIGNALS",
                style = MaterialTheme.typography.labelSmall,
                color = PukaarColors.TextSecondary
            )
        }

        items(messages) { msg ->
            GlowCard(
                glowColor = PukaarColors.AccentRed,
                modifier = Modifier.fillMaxWidth()
            ) {
                Column {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            StatusDot(color = PukaarColors.AccentRed)
                            Text(
                                text = msg.emergencyType,
                                fontFamily = RajdhaniFontFamily,
                                fontWeight = FontWeight.Bold,
                                fontSize = 18.sp,
                                color = PukaarColors.AccentRed
                            )
                        }

                        Text(
                            text = "${msg.hopCount} Hops",
                            style = MaterialTheme.typography.labelSmall,
                            color = PukaarColors.TextSecondary
                        )
                    }

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        text = "Sender: ${msg.senderName} (${msg.victimCount} persons)",
                        fontFamily = RajdhaniFontFamily,
                        fontWeight = FontWeight.Bold,
                        fontSize = 16.sp,
                        color = PukaarColors.TextPrimary
                    )

                    Spacer(modifier = Modifier.height(2.dp))

                    Text(
                        text = msg.notes,
                        style = MaterialTheme.typography.bodyMedium,
                        color = PukaarColors.TextPrimary
                    )

                    Spacer(modifier = Modifier.height(6.dp))

                    Text(
                        text = "GPS: ${msg.latitude}°N, ${msg.longitude}°E • STATUS: ${msg.status.name}",
                        style = MaterialTheme.typography.labelSmall,
                        color = PukaarColors.AccentCyan
                    )
                }
            }
        }

        item {
            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}
