package com.pukaar.android.ui.screens.sos.inbox

import android.content.Intent
import android.net.Uri
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pukaar.android.domain.model.EmergencyType
import com.pukaar.android.domain.model.IncomingSos
import com.pukaar.android.domain.model.RelayStatus
import com.pukaar.android.domain.model.VerificationStatus
import com.pukaar.android.ui.components.GlowCard
import com.pukaar.android.ui.components.StatusDot
import com.pukaar.android.ui.theme.JetBrainsMonoFamily
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily

@Composable
fun SosInboxScreen(
    viewModel: SosInboxViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(PukaarColors.BgVoid)
    ) {
        if (state.incoming.isEmpty()) {
            EmptyInboxState()
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(state.incoming, key = { it.msgId }) { sos ->
                    IncomingSosCard(
                        sos = sos,
                        onRelayNow = { viewModel.relayManually(sos.msgId) }
                    )
                    HorizontalDivider(
                        color = PukaarColors.AccentRed.copy(alpha = 0.10f),
                        thickness = 0.5.dp,
                        modifier = Modifier.padding(top = 8.dp)
                    )
                }

                item {
                    Spacer(modifier = Modifier.height(24.dp))
                }
            }
        }
    }
}

@Composable
private fun IncomingSosCard(
    sos: IncomingSos,
    onRelayNow: () -> Unit
) {
    val context = LocalContext.current

    GlowCard(
        glowColor = PukaarColors.AccentRed,
        cornerRadius = 12.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            // Top Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // Large AccentRed SOS Badge
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(6.dp))
                            .background(PukaarColors.AccentRed)
                            .padding(horizontal = 8.dp, vertical = 3.dp)
                    ) {
                        Text(
                            text = "SOS",
                            fontFamily = RajdhaniFontFamily,
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp,
                            color = Color.White
                        )
                    }

                    // Emergency Type Chip
                    EmergencyTypeChip(type = sos.emergencyType)
                }

                Text(
                    text = formatRelativeTime(sos.receivedAt),
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 10.sp,
                    color = PukaarColors.TextSecondary
                )
            }

            // Sender Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "FROM: ${sos.senderHash}",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = PukaarColors.AccentAmber
                )

                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        text = "VIA ${sos.transport.name}",
                        fontFamily = JetBrainsMonoFamily,
                        fontSize = 10.sp,
                        color = PukaarColors.TextSecondary
                    )
                    Text(
                        text = "• ${sos.hopCount} HOP(s)",
                        fontFamily = JetBrainsMonoFamily,
                        fontSize = 10.sp,
                        color = PukaarColors.TextSecondary
                    )
                }
            }

            // Location Row (if lat/lon not null)
            if (sos.latitude != null && sos.longitude != null) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.LocationOn,
                            contentDescription = "Location",
                            tint = PukaarColors.AccentCyan,
                            modifier = Modifier.size(16.dp)
                        )
                        Text(
                            text = "${String.format("%.4f", sos.latitude)}° N, ${String.format("%.4f", sos.longitude)}° E",
                            fontFamily = JetBrainsMonoFamily,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = PukaarColors.TextPrimary
                        )
                    }

                    TextButton(
                        onClick = {
                            val uri = Uri.parse("geo:${sos.latitude},${sos.longitude}?q=${sos.latitude},${sos.longitude}(Emergency+SOS)")
                            val intent = Intent(Intent.ACTION_VIEW, uri)
                            try {
                                context.startActivity(intent)
                            } catch (e: Exception) {
                                // Ignore or browser fallback
                            }
                        }
                    ) {
                        Text(
                            text = "OPEN IN MAPS",
                            fontFamily = JetBrainsMonoFamily,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            color = PukaarColors.AccentCyan
                        )
                    }
                }
            }

            // Message (if not null)
            if (!sos.message.isNullOrBlank()) {
                Text(
                    text = "\"${sos.message}\"",
                    fontStyle = FontStyle.Italic,
                    fontSize = 13.sp,
                    color = PukaarColors.TextSecondary,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
            }

            // Footer Row: Relay Status + Verification
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                RelayStatusBadge(status = sos.relayStatus)
                VerificationBadge(status = sos.verificationStatus)
            }

            // Manual Relay Button if Pending
            if (sos.relayStatus == RelayStatus.PENDING) {
                OutlinedButton(
                    onClick = onRelayNow,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(42.dp),
                    shape = RoundedCornerShape(8.dp),
                    border = BorderStroke(1.dp, PukaarColors.AccentRed),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = PukaarColors.AccentRed)
                ) {
                    Text(
                        text = "RELAY NOW",
                        fontFamily = RajdhaniFontFamily,
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp,
                        letterSpacing = 1.sp
                    )
                }
            }
        }
    }
}

@Composable
private fun EmergencyTypeChip(type: EmergencyType) {
    val (color, label) = when (type) {
        EmergencyType.MEDICAL -> Pair(PukaarColors.AccentCyan, "MEDICAL")
        EmergencyType.TRAPPED -> Pair(PukaarColors.AccentAmber, "TRAPPED")
        EmergencyType.FLOOD -> Pair(PukaarColors.AccentCyan, "FLOOD")
        EmergencyType.OTHER -> Pair(PukaarColors.TextSecondary, "OTHER")
    }

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(6.dp))
            .background(color.copy(alpha = 0.15f))
            .border(1.dp, color.copy(alpha = 0.6f), RoundedCornerShape(6.dp))
            .padding(horizontal = 8.dp, vertical = 2.dp)
    ) {
        Text(
            text = label,
            fontFamily = JetBrainsMonoFamily,
            fontSize = 10.sp,
            fontWeight = FontWeight.Bold,
            color = color
        )
    }
}

@Composable
private fun RelayStatusBadge(status: RelayStatus) {
    val (color, label) = when (status) {
        RelayStatus.RELAYED -> Pair(PukaarColors.AccentGreen, "RELAYED ✓")
        RelayStatus.PENDING -> Pair(PukaarColors.AccentAmber, "RELAY PENDING")
        RelayStatus.TTL_EXHAUSTED -> Pair(PukaarColors.TextSecondary, "TTL EXHAUSTED")
        RelayStatus.RELAY_FAILED -> Pair(PukaarColors.AccentRed, "RELAY FAILED")
    }

    Text(
        text = label,
        fontFamily = JetBrainsMonoFamily,
        fontSize = 10.sp,
        fontWeight = FontWeight.Bold,
        color = color
    )
}

@Composable
private fun VerificationBadge(status: VerificationStatus) {
    val (color, label) = when (status) {
        VerificationStatus.VERIFIED -> Pair(PukaarColors.AccentGreen, "✓ VERIFIED")
        VerificationStatus.UNVERIFIED -> Pair(PukaarColors.AccentAmber, "? UNVERIFIED")
        VerificationStatus.INVALID -> Pair(PukaarColors.AccentRed, "✗ INVALID")
        VerificationStatus.PENDING -> Pair(PukaarColors.TextSecondary, "◌ CHECKING")
    }

    Text(
        text = label,
        fontFamily = JetBrainsMonoFamily,
        fontSize = 10.sp,
        fontWeight = FontWeight.Bold,
        color = color
    )
}

private fun formatRelativeTime(receivedAt: Long): String {
    val diff = System.currentTimeMillis() - receivedAt
    val mins = diff / (60 * 1000)
    val hours = mins / 60
    return when {
        mins < 1 -> "just now"
        mins < 60 -> "${mins}m ago"
        hours < 24 -> "${hours}h ago"
        else -> "${hours / 24}d ago"
    }
}

@Composable
private fun EmptyInboxState() {
    val transition = rememberInfiniteTransition(label = "radar_empty_inbox")
    val angle by transition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(2500, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "radar_angle"
    )

    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.size(200.dp)) {
            val center = Offset(size.width / 2f, size.height / 2f)
            val maxRadius = size.minDimension / 2f

            drawCircle(
                color = PukaarColors.AccentCyan.copy(alpha = 0.05f),
                radius = maxRadius,
                style = Stroke(width = 1.5.dp.toPx())
            )
            drawCircle(
                color = PukaarColors.AccentCyan.copy(alpha = 0.03f),
                radius = maxRadius * 0.66f,
                style = Stroke(width = 1.5.dp.toPx())
            )
            drawCircle(
                color = PukaarColors.AccentCyan.copy(alpha = 0.01f),
                radius = maxRadius * 0.33f,
                style = Stroke(width = 1.5.dp.toPx())
            )

            drawArc(
                brush = Brush.sweepGradient(
                    colors = listOf(
                        Color.Transparent,
                        PukaarColors.AccentCyan.copy(alpha = 0.35f)
                    ),
                    center = center
                ),
                startAngle = angle,
                sweepAngle = 40f,
                useCenter = true,
                topLeft = Offset(center.x - maxRadius, center.y - maxRadius),
                size = Size(maxRadius * 2, maxRadius * 2)
            )
        }

        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(top = 240.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "LISTENING FOR EMERGENCY SIGNALS",
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 14.sp,
                letterSpacing = 1.sp,
                color = PukaarColors.TextSecondary
            )

            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                StatusDot(color = PukaarColors.AccentGreen)
                Text(
                    text = "MESH ACTIVE",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = PukaarColors.AccentGreen
                )
            }
        }
    }
}
