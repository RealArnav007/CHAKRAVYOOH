package com.pukaar.android.ui.screens.mesh

import android.graphics.Paint
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bluetooth
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.filled.Wifi
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pukaar.android.domain.model.DeliveryStatus
import com.pukaar.android.domain.model.GatewayStatus
import com.pukaar.android.domain.model.MeshTransport
import com.pukaar.android.domain.model.MessageType
import com.pukaar.android.domain.model.PacketLogEntry
import com.pukaar.android.domain.model.PacketLogStatus
import com.pukaar.android.ui.components.DataLabel
import com.pukaar.android.ui.components.GlowCard
import com.pukaar.android.ui.components.StatusDot
import com.pukaar.android.ui.theme.JetBrainsMonoFamily
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily
import kotlin.math.cos
import kotlin.math.sin

@Composable
fun MeshStatusScreen(
    viewModel: MeshStatusViewModel = hiltViewModel(),
    onNavigateToSettings: () -> Unit = {}
) {
    val state by viewModel.state.collectAsState()

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(PukaarColors.BgVoid)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Permission Warning if missing
        if (!state.hasPermissions) {
            item {
                PermissionWarningCard(onGrant = { viewModel.setPermissionGranted(true) })
            }
        }

        // Section 1: Status Grid (2x2)
        item {
            MeshStatusGrid(state = state)
        }

        // Section 2: Interactive Node Graph (Canvas 200dp)
        item {
            GlowCard(
                glowColor = PukaarColors.AccentCyan,
                cornerRadius = 12.dp,
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.fillMaxWidth()) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "LIVE MESH TOPOLOGY",
                            fontFamily = RajdhaniFontFamily,
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp,
                            letterSpacing = 1.sp,
                            color = PukaarColors.TextPrimary
                        )

                        Text(
                            text = "${state.nearbyDevices.size} PEERS DETECTED",
                            fontFamily = JetBrainsMonoFamily,
                            fontSize = 10.sp,
                            color = PukaarColors.AccentCyan
                        )
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    MeshTopologyCanvas(
                        nearbyDevices = state.nearbyDevices,
                        isGatewayConnected = state.status.gatewayStatus == GatewayStatus.CONNECTED,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(190.dp)
                    )
                }
            }
        }

        // Section 3: Delivery Status Banner
        item {
            DeliveryStatusBanner(deliveryStatus = state.status.deliveryStatus)
        }

        // Section 4: Packet Activity Log
        item {
            PacketActivityLogCard(packetLog = state.packetLog)
        }

        // Section 5: Stats Footer
        item {
            MeshStatsFooterCard(
                duplicates = state.droppedDuplicates,
                ttlExpired = state.ttlExpired,
                invalidSig = state.invalidSig
            )
        }

        item {
            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}

@Composable
private fun PermissionWarningCard(onGrant: () -> Unit) {
    GlowCard(
        glowColor = PukaarColors.AccentAmber,
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
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.weight(1f)
            ) {
                Icon(
                    imageVector = Icons.Default.Warning,
                    contentDescription = null,
                    tint = PukaarColors.AccentAmber,
                    modifier = Modifier.size(20.dp)
                )
                Text(
                    text = "BLUETOOTH + WI-FI AWARE REQUIRED FOR MESH",
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp,
                    color = PukaarColors.AccentAmber
                )
            }

            TextButton(onClick = onGrant) {
                Text(
                    text = "GRANT",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = PukaarColors.AccentCyan
                )
            }
        }
    }
}

@Composable
private fun MeshStatusGrid(state: MeshStatusState) {
    val internetColor = if (state.status.internetOnline) PukaarColors.AccentGreen else PukaarColors.AccentRed
    val meshColor = if (state.status.meshActive) PukaarColors.AccentGreen else PukaarColors.TextSecondary
    val relayColor = if (state.status.nearbyRelayCount > 0) PukaarColors.AccentCyan else PukaarColors.TextSecondary
    val gatewayColor = when (state.status.gatewayStatus) {
        GatewayStatus.CONNECTED -> PukaarColors.AccentGreen
        GatewayStatus.SEARCHING -> PukaarColors.AccentAmber
        GatewayStatus.UNAVAILABLE -> PukaarColors.AccentRed
    }

    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // Row 1: Internet & Mesh
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Cell: INTERNET
            GlowCard(
                glowColor = internetColor,
                modifier = Modifier.weight(1f).height(90.dp)
            ) {
                Column(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        DataLabel(label = "INTERNET", value = if (state.status.internetOnline) "ONLINE" else "OFFLINE", valueColor = internetColor)
                        StatusDot(color = internetColor)
                    }
                }
            }

            // Cell: MESH
            GlowCard(
                glowColor = meshColor,
                modifier = Modifier.weight(1f).height(90.dp)
            ) {
                Column(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        DataLabel(label = "MESH", value = if (state.status.meshActive) "ACTIVE" else "INACTIVE", valueColor = meshColor)
                        StatusDot(color = meshColor)
                    }
                    Text(
                        text = "BT + WI-FI AWARE",
                        fontFamily = JetBrainsMonoFamily,
                        fontSize = 9.sp,
                        color = PukaarColors.TextSecondary
                    )
                }
            }
        }

        // Row 2: Relays & Gateway
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Cell: RELAYS
            GlowCard(
                glowColor = relayColor,
                modifier = Modifier.weight(1f).height(90.dp)
            ) {
                Column(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    DataLabel(label = "RELAYS", value = "${state.status.nearbyRelayCount}", valueColor = relayColor)
                    Text(
                        text = "NEARBY NODES",
                        fontFamily = JetBrainsMonoFamily,
                        fontSize = 9.sp,
                        color = PukaarColors.TextSecondary
                    )
                }
            }

            // Cell: GATEWAY
            GlowCard(
                glowColor = gatewayColor,
                modifier = Modifier.weight(1f).height(90.dp)
            ) {
                Column(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    DataLabel(label = "GATEWAY", value = state.status.gatewayStatus.name, valueColor = gatewayColor)
                    StatusDot(color = gatewayColor)
                }
            }
        }
    }
}

@Composable
private fun MeshTopologyCanvas(
    nearbyDevices: List<RelayDevice>,
    isGatewayConnected: Boolean,
    modifier: Modifier = Modifier
) {
    val density = LocalDensity.current
    val transition = rememberInfiniteTransition(label = "particle_flow")
    val particleProgress by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(1800, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "particle_anim"
    )

    val pulseTransition = rememberInfiniteTransition(label = "center_pulse")
    val centerScale by pulseTransition.animateFloat(
        initialValue = 1.0f,
        targetValue = 1.3f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse_scale"
    )

    Canvas(modifier = modifier) {
        val width = size.width
        val height = size.height

        val centerPos = Offset(width / 2f, height - 35.dp.toPx())
        val centerRadius = 20.dp.toPx()

        // 1. Surrounding Nearby Nodes in Semicircle
        val displayDevices = nearbyDevices.take(6)
        val numNodes = displayDevices.size
        val arcRadius = height * 0.62f
        val nodePositions = mutableListOf<Offset>()

        displayDevices.forEachIndexed { index, device ->
            // Distribute angles evenly from 195 deg to 345 deg
            val angleDeg = if (numNodes == 1) 270.0 else 195.0 + (150.0 / (numNodes - 1)) * index
            val angleRad = Math.toRadians(angleDeg)
            val nodeX = (centerPos.x + arcRadius * cos(angleRad)).toFloat()
            val nodeY = (centerPos.y + arcRadius * sin(angleRad)).toFloat()
            val nodePos = Offset(nodeX, nodeY)
            nodePositions.add(nodePos)

            // Draw connection line
            val isBt = device.transport == MeshTransport.BLUETOOTH
            val pathEffect = if (isBt) null else PathEffect.dashPathEffect(floatArrayOf(10f, 10f), 0f)

            drawLine(
                color = PukaarColors.AccentCyan.copy(alpha = 0.5f),
                start = centerPos,
                end = nodePos,
                strokeWidth = 1.5.dp.toPx(),
                pathEffect = pathEffect
            )

            // Animated Particle along connection line
            val particleFraction = (particleProgress + (index.toFloat() / (numNodes.coerceAtLeast(1)))) % 1f
            val particleX = centerPos.x + (nodePos.x - centerPos.x) * particleFraction
            val particleY = centerPos.y + (nodePos.y - centerPos.y) * particleFraction
            val particleAlpha = (sin(particleFraction * Math.PI)).toFloat().coerceIn(0f, 1f)

            drawCircle(
                color = PukaarColors.AccentCyan.copy(alpha = particleAlpha),
                radius = 3.5.dp.toPx(),
                center = Offset(particleX, particleY)
            )

            // Node Age Color
            val ageMs = System.currentTimeMillis() - device.lastSeenMs
            val nodeColor = when {
                ageMs < 5000 -> PukaarColors.AccentGreen
                ageMs < 30000 -> PukaarColors.AccentAmber
                else -> PukaarColors.TextSecondary
            }

            // Draw Node Circle
            drawCircle(
                color = nodeColor,
                radius = 14.dp.toPx(),
                center = nodePos
            )
            drawCircle(
                color = PukaarColors.BgVoid,
                radius = 10.dp.toPx(),
                center = nodePos
            )
            drawCircle(
                color = nodeColor,
                radius = 5.dp.toPx(),
                center = nodePos
            )

            // Node ID Label
            val label = device.anonymizedId.take(6)
            drawContext.canvas.nativeCanvas.apply {
                val paint = Paint().apply {
                    color = Color.White.toArgb()
                    textSize = 8.sp.toPx()
                    textAlign = Paint.Align.CENTER
                    isAntiAlias = true
                }
                drawText(label, nodePos.x, nodePos.y - 18.dp.toPx(), paint)
            }
        }

        // 2. Gateway Node (if connected)
        if (isGatewayConnected) {
            val gatewayPos = Offset(width - 28.dp.toPx(), 45.dp.toPx())

            // Line from center to gateway
            drawLine(
                color = PukaarColors.AccentGreen.copy(alpha = 0.6f),
                start = centerPos,
                end = gatewayPos,
                strokeWidth = 2.dp.toPx()
            )

            // Draw Gateway Rect
            drawRoundRect(
                color = PukaarColors.AccentGreen,
                topLeft = Offset(gatewayPos.x - 14.dp.toPx(), gatewayPos.y - 10.dp.toPx()),
                size = Size(28.dp.toPx(), 20.dp.toPx()),
                cornerRadius = androidx.compose.ui.geometry.CornerRadius(4.dp.toPx(), 4.dp.toPx())
            )

            drawContext.canvas.nativeCanvas.apply {
                val paint = Paint().apply {
                    color = PukaarColors.BgVoid.toArgb()
                    textSize = 9.sp.toPx()
                    textAlign = Paint.Align.CENTER
                    isFakeBoldText = true
                    isAntiAlias = true
                }
                drawText("GTW", gatewayPos.x, gatewayPos.y + 3.dp.toPx(), paint)

                val backendPaint = Paint().apply {
                    color = PukaarColors.AccentGreen.toArgb()
                    textSize = 8.sp.toPx()
                    textAlign = Paint.Align.RIGHT
                    isAntiAlias = true
                }
                drawText("→ BACKEND", width, gatewayPos.y - 12.dp.toPx(), backendPaint)
            }
        }

        // 3. Center Node ("YOU")
        // Concentric outer halo
        drawCircle(
            color = PukaarColors.AccentCyan.copy(alpha = 0.15f),
            radius = centerRadius * centerScale,
            center = centerPos,
            style = Stroke(width = 2.dp.toPx())
        )
        drawCircle(
            color = PukaarColors.AccentCyan.copy(alpha = 0.35f),
            radius = centerRadius * (1.0f + (centerScale - 1.0f) * 0.5f),
            center = centerPos,
            style = Stroke(width = 1.5.dp.toPx())
        )
        // Solid Center Circle
        drawCircle(
            color = PukaarColors.AccentCyan,
            radius = centerRadius,
            center = centerPos
        )

        drawContext.canvas.nativeCanvas.apply {
            val paint = Paint().apply {
                color = PukaarColors.BgVoid.toArgb()
                textSize = 10.sp.toPx()
                textAlign = Paint.Align.CENTER
                isFakeBoldText = true
                isAntiAlias = true
            }
            drawText("YOU", centerPos.x, centerPos.y + 3.5.dp.toPx(), paint)
        }
    }
}

@Composable
private fun DeliveryStatusBanner(deliveryStatus: DeliveryStatus) {
    val (statusColor, statusText) = when (deliveryStatus) {
        DeliveryStatus.DELIVERED -> Pair(PukaarColors.AccentGreen, "DELIVERED")
        DeliveryStatus.PENDING -> Pair(PukaarColors.AccentAmber, "PENDING")
        DeliveryStatus.FAILED -> Pair(PukaarColors.AccentRed, "FAILED")
        DeliveryStatus.NOT_SENT -> Pair(PukaarColors.TextSecondary, "NOT SENT")
    }

    GlowCard(
        glowColor = statusColor,
        cornerRadius = 10.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "DELIVERY STATUS:",
                fontFamily = JetBrainsMonoFamily,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = PukaarColors.TextSecondary
            )

            Text(
                text = statusText,
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                letterSpacing = 1.sp,
                color = statusColor
            )
        }
    }
}

@Composable
private fun PacketActivityLogCard(packetLog: List<PacketLogEntry>) {
    GlowCard(
        glowColor = PukaarColors.AccentCyan,
        cornerRadius = 12.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "PACKET ACTIVITY",
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp,
                    color = PukaarColors.TextPrimary
                )

                Text(
                    text = "(LAST 50)",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 10.sp,
                    color = PukaarColors.TextSecondary
                )
            }

            HorizontalDivider(
                color = PukaarColors.AccentCyan.copy(alpha = 0.2f),
                thickness = 0.5.dp
            )

            if (packetLog.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(80.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "NO PACKET TRAFFIC LOGGED",
                        fontFamily = JetBrainsMonoFamily,
                        fontSize = 11.sp,
                        color = PukaarColors.TextSecondary
                    )
                }
            } else {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(240.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    packetLog.take(7).forEach { entry ->
                        PacketLogRow(entry = entry)
                    }
                }
            }
        }
    }
}

@Composable
private fun PacketLogRow(entry: PacketLogEntry) {
    val (badgeBg, badgeText) = when (entry.type) {
        MessageType.SOS -> Pair(PukaarColors.AccentRed, "SOS")
        MessageType.CYCLONE_WARNING -> Pair(PukaarColors.AccentAmber, "WARN")
        MessageType.RELAY -> Pair(PukaarColors.AccentCyan, "RELAY")
        MessageType.INFORMATIONAL -> Pair(PukaarColors.TextSecondary, "INFO")
    }

    val (statusColor, statusLabel) = when (entry.status) {
        PacketLogStatus.RECEIVED -> Pair(PukaarColors.TextPrimary, "RECEIVED")
        PacketLogStatus.RELAYED -> Pair(PukaarColors.AccentGreen, "↑ RELAYED")
        PacketLogStatus.DROPPED_DUPLICATE -> Pair(PukaarColors.AccentAmber, "⟳ DUP")
        PacketLogStatus.DROPPED_TTL -> Pair(PukaarColors.AccentRed, "↯ TTL=0")
        PacketLogStatus.DROPPED_INVALID_SIG -> Pair(PukaarColors.AccentRed, "✗ SIG")
        PacketLogStatus.DELIVERED -> Pair(PukaarColors.AccentGreen, "✓ DELIVERED")
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(32.dp)
            .clip(RoundedCornerShape(4.dp))
            .background(PukaarColors.BgElevated.copy(alpha = 0.5f))
            .padding(horizontal = 8.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(3.dp))
                    .background(badgeBg.copy(alpha = 0.2f))
                    .border(0.5.dp, badgeBg, RoundedCornerShape(3.dp))
                    .padding(horizontal = 4.dp, vertical = 1.dp)
            ) {
                Text(
                    text = badgeText,
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 8.sp,
                    color = badgeBg
                )
            }

            Text(
                text = entry.msgId.take(8),
                fontFamily = JetBrainsMonoFamily,
                fontSize = 10.sp,
                color = PukaarColors.TextSecondary
            )
        }

        Text(
            text = statusLabel,
            fontFamily = JetBrainsMonoFamily,
            fontSize = 10.sp,
            fontWeight = FontWeight.Bold,
            color = statusColor
        )

        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            Text(
                text = formatLogTime(entry.timestamp),
                fontFamily = JetBrainsMonoFamily,
                fontSize = 9.sp,
                color = PukaarColors.TextSecondary
            )

            Icon(
                imageVector = if (entry.transport == MeshTransport.BLUETOOTH) Icons.Default.Bluetooth else Icons.Default.Wifi,
                contentDescription = null,
                tint = PukaarColors.TextSecondary,
                modifier = Modifier.size(12.dp)
            )
        }
    }
}

@Composable
private fun MeshStatsFooterCard(
    duplicates: Int,
    ttlExpired: Int,
    invalidSig: Int
) {
    GlowCard(
        glowColor = PukaarColors.AccentCyan,
        cornerRadius = 10.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceAround,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "DUPLICATES DROPPED",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 9.sp,
                    color = PukaarColors.TextSecondary
                )
                Text(
                    text = "$duplicates",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                    color = PukaarColors.AccentAmber
                )
            }

            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "TTL EXPIRED",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 9.sp,
                    color = PukaarColors.TextSecondary
                )
                Text(
                    text = "$ttlExpired",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                    color = PukaarColors.AccentRed
                )
            }

            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "INVALID SIG",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 9.sp,
                    color = PukaarColors.TextSecondary
                )
                Text(
                    text = "$invalidSig",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                    color = PukaarColors.AccentRed
                )
            }
        }
    }
}

private fun formatLogTime(timestamp: Long): String {
    val diff = (System.currentTimeMillis() - timestamp) / 1000
    return if (diff < 60) "${diff}s ago" else "${diff / 60}m ago"
}
