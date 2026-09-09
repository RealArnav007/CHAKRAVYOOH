package com.pukaar.android.ui.screens.sos.send

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Fingerprint
import androidx.compose.material.icons.filled.HelpOutline
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.MedicalServices
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.filled.WaterDamage
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pukaar.android.domain.model.EmergencyType
import com.pukaar.android.ui.components.GlowCard
import com.pukaar.android.ui.components.StatusDot
import com.pukaar.android.ui.theme.JetBrainsMonoFamily
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily

@Composable
fun SosSendScreen(
    viewModel: SosSendViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(PukaarColors.BgVoid)
            .padding(16.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // 1. Header
        Column(modifier = Modifier.fillMaxWidth()) {
            Text(
                text = "EMERGENCY SOS",
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 32.sp,
                letterSpacing = 1.5.sp,
                color = PukaarColors.AccentRed
            )
            Text(
                text = "Har pukar, kisi tak",
                fontStyle = FontStyle.Italic,
                fontSize = 12.sp,
                color = PukaarColors.TextSecondary
            )
        }

        // 2. Emergency Type Grid (2x2)
        EmergencyTypeGrid(
            selectedType = state.emergencyType,
            onTypeSelected = { viewModel.setEmergencyType(it) }
        )

        // 3. Location Row
        LocationRow(
            latitude = state.latitude,
            longitude = state.longitude,
            onGrantOrMock = {
                viewModel.setLocation(19.8135, 85.8312)
            }
        )

        // 4. Message Field
        OutlinedTextField(
            value = state.message,
            onValueChange = { viewModel.setMessage(it) },
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(8.dp)),
            placeholder = {
                Text(
                    text = "Additional details (optional)",
                    color = PukaarColors.TextSecondary.copy(alpha = 0.6f),
                    fontSize = 14.sp
                )
            },
            colors = OutlinedTextFieldDefaults.colors(
                focusedContainerColor = PukaarColors.BgElevated,
                unfocusedContainerColor = PukaarColors.BgElevated,
                focusedBorderColor = PukaarColors.AccentCyan.copy(alpha = 0.4f),
                unfocusedBorderColor = PukaarColors.TextSecondary.copy(alpha = 0.2f),
                cursorColor = PukaarColors.AccentRed,
                focusedTextColor = PukaarColors.TextPrimary,
                unfocusedTextColor = PukaarColors.TextPrimary
            ),
            shape = RoundedCornerShape(8.dp),
            minLines = 2,
            maxLines = 3
        )

        // 5. Sensitive Data Toggle
        SensitiveDataToggleCard(
            hasSensitiveData = state.hasSensitiveData,
            onToggle = { viewModel.setSensitiveData(it) }
        )

        // 6. Delivery Path Indicator (visible when sendStatus != IDLE)
        AnimatedVisibility(visible = state.sendStatus != SendStatus.IDLE) {
            DeliveryPathIndicator(
                sendStatus = state.sendStatus,
                activePath = state.activeDeliveryPath
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        // 7. Send Button
        SosSendButton(
            sendStatus = state.sendStatus,
            activeDeliveryPath = state.activeDeliveryPath,
            onClick = { viewModel.sendSos() }
        )

        Spacer(modifier = Modifier.height(24.dp))
    }
}

@Composable
private fun EmergencyTypeGrid(
    selectedType: EmergencyType,
    onTypeSelected: (EmergencyType) -> Unit
) {
    val types = listOf(
        Triple(EmergencyType.MEDICAL, "MEDICAL", Icons.Default.MedicalServices),
        Triple(EmergencyType.TRAPPED, "TRAPPED", Icons.Default.Warning),
        Triple(EmergencyType.FLOOD, "FLOOD", Icons.Default.WaterDamage),
        Triple(EmergencyType.OTHER, "OTHER", Icons.Default.HelpOutline)
    )

    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            EmergencyTypeCard(
                type = types[0].first,
                label = types[0].second,
                icon = types[0].third,
                isSelected = selectedType == types[0].first,
                onSelect = { onTypeSelected(types[0].first) },
                modifier = Modifier.weight(1f)
            )
            EmergencyTypeCard(
                type = types[1].first,
                label = types[1].second,
                icon = types[1].third,
                isSelected = selectedType == types[1].first,
                onSelect = { onTypeSelected(types[1].first) },
                modifier = Modifier.weight(1f)
            )
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            EmergencyTypeCard(
                type = types[2].first,
                label = types[2].second,
                icon = types[2].third,
                isSelected = selectedType == types[2].first,
                onSelect = { onTypeSelected(types[2].first) },
                modifier = Modifier.weight(1f)
            )
            EmergencyTypeCard(
                type = types[3].first,
                label = types[3].second,
                icon = types[3].third,
                isSelected = selectedType == types[3].first,
                onSelect = { onTypeSelected(types[3].first) },
                modifier = Modifier.weight(1f)
            )
        }
    }
}

@Composable
private fun EmergencyTypeCard(
    type: EmergencyType,
    label: String,
    icon: ImageVector,
    isSelected: Boolean,
    onSelect: () -> Unit,
    modifier: Modifier = Modifier
) {
    val borderColor = if (isSelected) PukaarColors.AccentRed else PukaarColors.TextSecondary.copy(alpha = 0.2f)
    val textColor = if (isSelected) PukaarColors.AccentRed else PukaarColors.TextPrimary
    val glowColor = if (isSelected) PukaarColors.AccentRed else Color.Transparent

    GlowCard(
        glowColor = glowColor,
        cornerRadius = 10.dp,
        modifier = modifier
            .height(84.dp)
            .border(if (isSelected) 1.5.dp else 0.5.dp, borderColor, RoundedCornerShape(10.dp))
            .clickable { onSelect() }
    ) {
        Row(
            modifier = Modifier.fillMaxSize(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Icon(
                imageVector = icon,
                contentDescription = label,
                tint = if (isSelected) PukaarColors.AccentRed else PukaarColors.AccentCyan,
                modifier = Modifier.size(28.dp)
            )

            Text(
                text = label,
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 16.sp,
                color = textColor
            )
        }
    }
}

@Composable
private fun LocationRow(
    latitude: Double?,
    longitude: Double?,
    onGrantOrMock: () -> Unit
) {
    GlowCard(
        glowColor = PukaarColors.AccentCyan,
        cornerRadius = 10.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.LocationOn,
                    contentDescription = "Location",
                    tint = PukaarColors.AccentCyan,
                    modifier = Modifier.size(24.dp)
                )

                if (latitude != null && longitude != null) {
                    Text(
                        text = "${String.format("%.4f", latitude)}° N, ${String.format("%.4f", longitude)}° E",
                        fontFamily = JetBrainsMonoFamily,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = PukaarColors.TextPrimary
                    )
                } else {
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        StatusDot(color = PukaarColors.AccentAmber)
                        Text(
                            text = "ACQUIRING LOCATION...",
                            fontFamily = JetBrainsMonoFamily,
                            fontSize = 12.sp,
                            color = PukaarColors.AccentAmber
                        )
                    }
                }
            }

            if (latitude == null) {
                OutlinedButton(
                    onClick = onGrantOrMock,
                    shape = RoundedCornerShape(6.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = PukaarColors.AccentCyan),
                    border = androidx.compose.foundation.BorderStroke(1.dp, PukaarColors.AccentCyan)
                ) {
                    Text(text = "GRANT", fontFamily = JetBrainsMonoFamily, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
private fun SensitiveDataToggleCard(
    hasSensitiveData: Boolean,
    onToggle: (Boolean) -> Unit
) {
    GlowCard(
        glowColor = if (hasSensitiveData) PukaarColors.AccentCyan else Color.Transparent,
        cornerRadius = 10.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                modifier = Modifier.weight(1f)
            ) {
                Icon(
                    imageVector = Icons.Default.Lock,
                    contentDescription = "Sensitive",
                    tint = if (hasSensitiveData) PukaarColors.AccentCyan else PukaarColors.TextSecondary,
                    modifier = Modifier.size(20.dp)
                )

                Column {
                    Text(
                        text = "Contains sensitive information",
                        fontFamily = RajdhaniFontFamily,
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp,
                        color = PukaarColors.TextPrimary
                    )
                    Text(
                        text = "Payload encrypted before transmission",
                        fontSize = 11.sp,
                        color = PukaarColors.TextSecondary
                    )
                }
            }

            Switch(
                checked = hasSensitiveData,
                onCheckedChange = onToggle,
                colors = SwitchDefaults.colors(
                    checkedThumbColor = PukaarColors.AccentCyan,
                    checkedTrackColor = PukaarColors.AccentCyan.copy(alpha = 0.3f),
                    uncheckedThumbColor = PukaarColors.TextSecondary,
                    uncheckedTrackColor = PukaarColors.BgElevated
                )
            )
        }
    }
}

@Composable
private fun DeliveryPathIndicator(
    sendStatus: SendStatus,
    activePath: DeliveryPath?
) {
    val nodes = listOf("SIGN", "INTERNET", "WI-FI MESH", "BT MESH")

    val nodeStates = when (sendStatus) {
        SendStatus.IDLE -> listOf(NodeState.PENDING, NodeState.PENDING, NodeState.PENDING, NodeState.PENDING)
        SendStatus.SIGNING -> listOf(NodeState.ACTIVE, NodeState.PENDING, NodeState.PENDING, NodeState.PENDING)
        SendStatus.SENDING_INTERNET -> listOf(NodeState.SUCCESS, NodeState.ACTIVE, NodeState.PENDING, NodeState.PENDING)
        SendStatus.SENDING_WIFI -> listOf(NodeState.SUCCESS, NodeState.FAILED, NodeState.ACTIVE, NodeState.PENDING)
        SendStatus.SENDING_BT -> listOf(NodeState.SUCCESS, NodeState.FAILED, NodeState.FAILED, NodeState.ACTIVE)
        SendStatus.DELIVERED -> when (activePath) {
            DeliveryPath.INTERNET -> listOf(NodeState.SUCCESS, NodeState.SUCCESS, NodeState.PENDING, NodeState.PENDING)
            DeliveryPath.WIFI_AWARE -> listOf(NodeState.SUCCESS, NodeState.FAILED, NodeState.SUCCESS, NodeState.PENDING)
            DeliveryPath.BLUETOOTH, null -> listOf(NodeState.SUCCESS, NodeState.FAILED, NodeState.FAILED, NodeState.SUCCESS)
        }
        SendStatus.FAILED -> listOf(NodeState.SUCCESS, NodeState.FAILED, NodeState.FAILED, NodeState.FAILED)
    }

    GlowCard(
        glowColor = PukaarColors.AccentCyan,
        cornerRadius = 10.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Text(
                text = "DISPATCH & RELAY PIPELINE",
                fontFamily = JetBrainsMonoFamily,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                color = PukaarColors.TextSecondary
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                nodes.forEachIndexed { index, label ->
                    DeliveryNode(
                        label = label,
                        state = nodeStates[index]
                    )

                    if (index < nodes.size - 1) {
                        val isConnected = nodeStates[index] == NodeState.SUCCESS || nodeStates[index] == NodeState.ACTIVE
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .height(2.dp)
                                .padding(horizontal = 4.dp)
                                .background(if (isConnected) PukaarColors.AccentCyan else PukaarColors.TextSecondary.copy(alpha = 0.3f))
                        )
                    }
                }
            }
        }
    }
}

private enum class NodeState {
    PENDING, ACTIVE, SUCCESS, FAILED
}

@Composable
private fun DeliveryNode(
    label: String,
    state: NodeState
) {
    val transition = rememberInfiniteTransition(label = "pulse_node")
    val pulseScale by transition.animateFloat(
        initialValue = 0.9f,
        targetValue = 1.15f,
        animationSpec = infiniteRepeatable(
            animation = tween(400, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse_scale"
    )

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        val sizeModifier = if (state == NodeState.ACTIVE) Modifier.size((32 * pulseScale).dp) else Modifier.size(32.dp)

        Box(
            modifier = sizeModifier
                .clip(CircleShape)
                .background(
                    when (state) {
                        NodeState.PENDING -> PukaarColors.BgElevated
                        NodeState.ACTIVE -> PukaarColors.AccentCyan
                        NodeState.SUCCESS -> PukaarColors.AccentGreen
                        NodeState.FAILED -> PukaarColors.AccentRed
                    }
                )
                .border(
                    width = if (state == NodeState.PENDING) 0.5.dp else 1.dp,
                    color = when (state) {
                        NodeState.PENDING -> PukaarColors.AccentCyan.copy(alpha = 0.5f)
                        NodeState.ACTIVE -> PukaarColors.AccentCyan
                        NodeState.SUCCESS -> PukaarColors.AccentGreen
                        NodeState.FAILED -> PukaarColors.AccentRed
                    },
                    shape = CircleShape
                ),
            contentAlignment = Alignment.Center
        ) {
            when (state) {
                NodeState.PENDING -> Box(modifier = Modifier.size(6.dp).clip(CircleShape).background(PukaarColors.TextSecondary))
                NodeState.ACTIVE -> Icon(Icons.Default.Fingerprint, contentDescription = null, tint = PukaarColors.BgVoid, modifier = Modifier.size(16.dp))
                NodeState.SUCCESS -> Icon(Icons.Default.Check, contentDescription = null, tint = PukaarColors.BgVoid, modifier = Modifier.size(16.dp))
                NodeState.FAILED -> Icon(Icons.Default.Close, contentDescription = null, tint = Color.White, modifier = Modifier.size(16.dp))
            }
        }

        Text(
            text = label,
            fontFamily = JetBrainsMonoFamily,
            fontSize = 9.sp,
            fontWeight = FontWeight.Bold,
            color = if (state == NodeState.ACTIVE || state == NodeState.SUCCESS) PukaarColors.TextPrimary else PukaarColors.TextSecondary
        )
    }
}

@Composable
private fun SosSendButton(
    sendStatus: SendStatus,
    activeDeliveryPath: DeliveryPath?,
    onClick: () -> Unit
) {
    val (buttonColor, buttonText) = when (sendStatus) {
        SendStatus.IDLE -> Pair(PukaarColors.AccentRed, "SEND SOS")
        SendStatus.SIGNING -> Pair(PukaarColors.AccentRed.copy(alpha = 0.8f), "DIGITALLY SIGNING...")
        SendStatus.SENDING_INTERNET -> Pair(PukaarColors.AccentCyan, "DISPATCHING VIA INTERNET...")
        SendStatus.SENDING_WIFI -> Pair(PukaarColors.AccentAmber, "RELAYING VIA WI-FI MESH...")
        SendStatus.SENDING_BT -> Pair(PukaarColors.AccentAmber, "RELAYING VIA BLUETOOTH LE...")
        SendStatus.DELIVERED -> {
            val pathName = when (activeDeliveryPath) {
                DeliveryPath.INTERNET -> "INTERNET"
                DeliveryPath.WIFI_AWARE -> "WI-FI MESH"
                DeliveryPath.BLUETOOTH, null -> "BLUETOOTH LE"
            }
            Pair(PukaarColors.AccentGreen, "✓ SOS DELIVERED • $pathName")
        }
        SendStatus.FAILED -> Pair(Color(0xFF8B0000), "FAILED — CHECK MESH STATUS")
    }

    val glowAlpha = if (sendStatus == SendStatus.IDLE) 0.35f else 0.0f

    Button(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .height(64.dp)
            .drawBehind {
                if (glowAlpha > 0f) {
                    val stroke = 4.dp.toPx()
                    drawRoundRect(
                        color = PukaarColors.AccentRed.copy(alpha = 0.15f),
                        topLeft = Offset(-stroke * 2, -stroke * 2),
                        size = Size(size.width + stroke * 4, size.height + stroke * 4),
                        cornerRadius = androidx.compose.ui.geometry.CornerRadius(16.dp.toPx(), 16.dp.toPx()),
                        style = Stroke(width = stroke * 2)
                    )
                }
            },
        colors = ButtonDefaults.buttonColors(containerColor = buttonColor),
        shape = RoundedCornerShape(12.dp)
    ) {
        Text(
            text = buttonText,
            fontFamily = RajdhaniFontFamily,
            fontWeight = FontWeight.Bold,
            fontSize = 22.sp,
            letterSpacing = 1.5.sp,
            color = if (sendStatus == SendStatus.DELIVERED) PukaarColors.BgVoid else Color.White
        )
    }
}
