package com.pukaar.android.ui.screens.map

import android.content.Context
import android.graphics.Bitmap
import androidx.compose.animation.core.FastOutSlowInEasing
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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.BottomSheetScaffold
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.rememberBottomSheetScaffoldState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.model.BitmapDescriptor
import com.google.android.gms.maps.model.BitmapDescriptorFactory
import com.google.android.gms.maps.model.CameraPosition
import com.google.android.gms.maps.model.Dot
import com.google.android.gms.maps.model.Gap
import com.google.android.gms.maps.model.LatLng as MapLatLng
import com.google.android.gms.maps.model.MapStyleOptions
import com.google.maps.android.compose.GoogleMap
import com.google.maps.android.compose.MapProperties
import com.google.maps.android.compose.MapType
import com.google.maps.android.compose.MapUiSettings
import com.google.maps.android.compose.Marker
import com.google.maps.android.compose.MarkerState
import com.google.maps.android.compose.Polygon
import com.google.maps.android.compose.Polyline
import com.google.maps.android.compose.rememberCameraPositionState
import com.pukaar.android.R
import com.pukaar.android.domain.model.CycloneIntelligence
import com.pukaar.android.domain.model.CycloneStage
import com.pukaar.android.domain.model.PathPoint
import com.pukaar.android.domain.model.RiskLevel
import com.pukaar.android.domain.model.RiskZone
import com.pukaar.android.ui.components.DataLabel
import com.pukaar.android.ui.components.GlowCard
import com.pukaar.android.ui.components.StatusDot
import com.pukaar.android.ui.theme.JetBrainsMonoFamily
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily
import java.time.Instant

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CycloneMapScreen(
    viewModel: CycloneMapViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val context = LocalContext.current
    val scaffoldState = rememberBottomSheetScaffoldState()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(state.error) {
        state.error?.let { msg ->
            snackbarHostState.showSnackbar(msg)
        }
    }

    BottomSheetScaffold(
        scaffoldState = scaffoldState,
        snackbarHost = {
            SnackbarHost(hostState = snackbarHostState) { data ->
                Surface(
                    color = PukaarColors.AccentRed,
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text(
                        text = data.visuals.message,
                        color = PukaarColors.TextPrimary,
                        modifier = Modifier.padding(12.dp)
                    )
                }
            }
        },
        sheetPeekHeight = 100.dp,
        sheetContainerColor = PukaarColors.BgSurface,
        sheetContentColor = PukaarColors.TextPrimary,
        sheetShape = RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp),
        sheetContent = {
            BottomSheetContent(
                intelligence = state.intelligence,
                selectedHour = state.selectedForecastHour,
                onHourSelected = { viewModel.selectForecastHour(it) }
            )
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .background(PukaarColors.BgVoid)
        ) {
            if (state.isLoading && state.intelligence == null) {
                RadarScanOverlay(text = "SCANNING FOR CYCLONE DATA")
            } else if (state.intelligence == null) {
                RadarScanOverlay(text = "NO ACTIVE CYCLONE DETECTED")
            } else {
                val intelligence = state.intelligence!!
                CycloneMap(
                    intelligence = intelligence,
                    riskZones = state.riskZones,
                    selectedForecastHour = state.selectedForecastHour,
                    context = context
                )
            }

            // Top Overlays
            TopMapOverlays(
                webSocketConnected = state.webSocketConnected,
                onRefresh = { viewModel.refresh() },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 16.dp, start = 16.dp, end = 16.dp)
                    .align(Alignment.TopCenter)
            )
        }
    }
}

@Composable
private fun CycloneMap(
    intelligence: CycloneIntelligence,
    riskZones: List<RiskZone>,
    selectedForecastHour: Int,
    context: Context
) {
    val initialPosition = remember(intelligence) {
        MapLatLng(intelligence.currentPosition.latitude, intelligence.currentPosition.longitude)
    }

    val cameraPositionState = rememberCameraPositionState {
        position = CameraPosition.fromLatLngZoom(initialPosition, 6.5f)
    }

    LaunchedEffect(intelligence.currentPosition) {
        cameraPositionState.animate(
            CameraUpdateFactory.newLatLngZoom(
                MapLatLng(intelligence.currentPosition.latitude, intelligence.currentPosition.longitude),
                6.5f
            )
        )
    }

    val mapStyleOptions = remember {
        try {
            val json = context.resources.openRawResource(R.raw.map_style_night)
                .bufferedReader()
                .use { it.readText() }
            MapStyleOptions(json)
        } catch (e: Exception) {
            null
        }
    }

    val mapProperties = remember(mapStyleOptions) {
        MapProperties(
            mapType = MapType.HYBRID,
            mapStyleOptions = mapStyleOptions,
            isTrafficEnabled = false
        )
    }

    val mapUiSettings = remember {
        MapUiSettings(
            compassEnabled = true,
            myLocationButtonEnabled = false,
            mapToolbarEnabled = false,
            zoomControlsEnabled = false
        )
    }

    // Outer pulse animation for crosshair
    val transition = rememberInfiniteTransition(label = "crosshair_pulse")
    val scaleAnim by transition.animateFloat(
        initialValue = 1.0f,
        targetValue = 1.4f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )

    val crosshairIcon = remember(scaleAnim) {
        createCrosshairBitmapDescriptor(context, scaleAnim)
    }

    val arrowIcon = remember {
        createArrowBitmapDescriptor(context)
    }

    // Historical track (4 points leading to current)
    val historicalTrack = remember(intelligence) {
        val currLat = intelligence.currentPosition.latitude
        val currLng = intelligence.currentPosition.longitude
        listOf(
            MapLatLng(currLat - 1.2, currLng - 1.5),
            MapLatLng(currLat - 0.8, currLng - 1.0),
            MapLatLng(currLat - 0.4, currLng - 0.5),
            MapLatLng(currLat, currLng)
        )
    }

    // Filter predicted path
    val filteredPath = remember(intelligence.predictedPath, selectedForecastHour) {
        intelligence.predictedPath.filter { it.forecastHour <= selectedForecastHour }
    }

    val pathColor = remember(intelligence.predictionConfidence) {
        when {
            intelligence.predictionConfidence >= 0.75 -> PukaarColors.AccentYellow
            intelligence.predictionConfidence >= 0.50 -> PukaarColors.AccentAmber
            else -> PukaarColors.AccentRed
        }
    }

    val uncertaintyPolygon = remember(filteredPath, intelligence.uncertaintyRadiusKm) {
        computeUncertaintyCone(filteredPath, intelligence.uncertaintyRadiusKm)
    }

    GoogleMap(
        modifier = Modifier.fillMaxSize(),
        cameraPositionState = cameraPositionState,
        properties = mapProperties,
        uiSettings = mapUiSettings
    ) {
        // 1. Risk Zone Polygons & Labels
        riskZones.forEach { zone ->
            val (fillColor, strokeColor, strokeWidth) = getRiskZoneStyle(zone.riskLevel)
            val polyPoints = zone.polygon.map { MapLatLng(it.latitude, it.longitude) }

            if (polyPoints.isNotEmpty()) {
                Polygon(
                    points = polyPoints,
                    fillColor = fillColor,
                    strokeColor = strokeColor,
                    strokeWidth = strokeWidth * context.resources.displayMetrics.density
                )

                // Centroid label marker
                val centroid = computeCentroid(polyPoints)
                val labelIcon = remember(zone.zoneName, zone.riskLevel) {
                    createTextLabelBitmapDescriptor(
                        context,
                        zone.zoneName,
                        strokeColor.value.toInt()
                    )
                }
                Marker(
                    state = MarkerState(position = centroid),
                    icon = labelIcon,
                    anchor = Offset(0.5f, 0.5f)
                )
            }
        }

        // 2. Uncertainty Cone Polygon
        if (uncertaintyPolygon.size >= 3) {
            Polygon(
                points = uncertaintyPolygon,
                fillColor = PukaarColors.AccentRed.copy(alpha = 0.12f),
                strokeColor = PukaarColors.AccentRed.copy(alpha = 0.25f),
                strokeWidth = 1.dp.value * context.resources.displayMetrics.density
            )
        }

        // 3. Historical Track (Dashed Polyline)
        Polyline(
            points = historicalTrack,
            color = PukaarColors.AccentCyan.copy(alpha = 0.40f),
            width = 4.dp.value * context.resources.displayMetrics.density,
            pattern = listOf(Dot(), Gap(15f))
        )

        // 4. Predicted Path Polyline
        val predictedMapPoints = listOf(MapLatLng(intelligence.currentPosition.latitude, intelligence.currentPosition.longitude)) +
                filteredPath.map { MapLatLng(it.latitude, it.longitude) }

        if (predictedMapPoints.size >= 2) {
            Polyline(
                points = predictedMapPoints,
                color = pathColor,
                width = 6.dp.value * context.resources.displayMetrics.density
            )

            // Directional arrow markers every 3 points
            filteredPath.forEachIndexed { index, pt ->
                if ((index + 1) % 3 == 0) {
                    Marker(
                        state = MarkerState(position = MapLatLng(pt.latitude, pt.longitude)),
                        icon = arrowIcon,
                        anchor = Offset(0.5f, 0.5f)
                    )
                }
            }
        }

        // 5. Current Position Crosshair Marker
        Marker(
            state = MarkerState(position = MapLatLng(intelligence.currentPosition.latitude, intelligence.currentPosition.longitude)),
            icon = crosshairIcon,
            anchor = Offset(0.5f, 0.5f),
            title = intelligence.cycloneId
        )
    }
}

@Composable
private fun TopMapOverlays(
    webSocketConnected: Boolean,
    onRefresh: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Top-left: Live WebSocket Chip
        GlowCard(
            glowColor = if (webSocketConnected) PukaarColors.AccentGreen else PukaarColors.AccentRed,
            cornerRadius = 20.dp,
            modifier = Modifier.height(38.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                StatusDot(
                    color = if (webSocketConnected) PukaarColors.AccentGreen else PukaarColors.AccentRed
                )
                Text(
                    text = if (webSocketConnected) "LIVE" else "OFFLINE",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = PukaarColors.TextPrimary
                )
            }
        }

        // Top-right: Refresh Button
        GlowCard(
            cornerRadius = 20.dp,
            modifier = Modifier.size(38.dp)
        ) {
            IconButton(
                onClick = onRefresh,
                modifier = Modifier.fillMaxSize()
            ) {
                Icon(
                    imageVector = Icons.Default.Refresh,
                    contentDescription = "Refresh Cyclone Data",
                    tint = PukaarColors.AccentCyan
                )
            }
        }
    }
}

@Composable
private fun BottomSheetContent(
    intelligence: CycloneIntelligence?,
    selectedHour: Int,
    onHourSelected: (Int) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .border(
                BorderStroke(1.dp, PukaarColors.AccentCyan.copy(alpha = 0.5f)),
                RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp)
            )
            .padding(20.dp)
    ) {
        if (intelligence == null) {
            Text(
                text = "No Cyclone Data Available",
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                color = PukaarColors.TextSecondary
            )
            return@Column
        }

        // Collapsed Peek Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = intelligence.cycloneId,
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp,
                    color = PukaarColors.TextPrimary
                )
                Spacer(modifier = Modifier.height(4.dp))
                StageChip(stage = intelligence.classificationStage)
            }

            Column(horizontalAlignment = Alignment.End) {
                val operationalConf = calculateOperationalConfidence(intelligence)
                Text(
                    text = "OPERATIONAL CONFIDENCE: $operationalConf%",
                    fontFamily = JetBrainsMonoFamily,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = PukaarColors.AccentCyan
                )
                Spacer(modifier = Modifier.height(4.dp))
                Icon(
                    imageVector = Icons.Default.KeyboardArrowUp,
                    contentDescription = "Expand sheet",
                    tint = PukaarColors.AccentCyan
                )
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Expanded Section 1: Confidence Grid
        Text(
            text = "CONFIDENCE METRICS",
            fontFamily = JetBrainsMonoFamily,
            fontSize = 11.sp,
            color = PukaarColors.TextSecondary
        )
        Spacer(modifier = Modifier.height(8.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            DataLabel(
                label = "AI CONFIDENCE",
                value = "${(intelligence.predictionConfidence * 100).toInt()}%",
                valueColor = PukaarColors.AccentCyan,
                modifier = Modifier.weight(1f)
            )
            DataLabel(
                label = "OPERATIONAL",
                value = "${calculateOperationalConfidence(intelligence)}%",
                valueColor = PukaarColors.AccentGreen,
                modifier = Modifier.weight(1f)
            )
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Expanded Section 2: Forecast Selector
        Text(
            text = "FORECAST HORIZON",
            fontFamily = JetBrainsMonoFamily,
            fontSize = 11.sp,
            color = PukaarColors.TextSecondary
        )
        Spacer(modifier = Modifier.height(8.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            listOf(6, 12, 24).forEach { hour ->
                val selected = selectedHour == hour
                OutlinedButton(
                    onClick = { onHourSelected(hour) },
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(8.dp),
                    colors = ButtonDefaults.outlinedButtonColors(
                        containerColor = if (selected) PukaarColors.AccentCyan else Color.Transparent,
                        contentColor = if (selected) PukaarColors.BgVoid else PukaarColors.AccentCyan
                    ),
                    border = BorderStroke(1.dp, PukaarColors.AccentCyan)
                ) {
                    Text(
                        text = "+${hour}H",
                        fontFamily = RajdhaniFontFamily,
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Expanded Section 3: Data Freshness
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Text(
                text = "DATA FRESHNESS:",
                fontFamily = JetBrainsMonoFamily,
                fontSize = 11.sp,
                color = PukaarColors.TextSecondary
            )
            DataFreshnessPill(validUntil = intelligence.validUntil)
        }

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
private fun StageChip(stage: CycloneStage) {
    val (color, text) = when (stage) {
        CycloneStage.DEVELOPING_DISTURBANCE -> Pair(PukaarColors.AccentCyan, "DISTURBANCE")
        CycloneStage.TROPICAL_DEPRESSION -> Pair(PukaarColors.AccentYellow, "DEPRESSION")
        CycloneStage.MATURE_TROPICAL_CYCLONE -> Pair(PukaarColors.AccentRed, "MATURE CYCLONE")
        CycloneStage.WEAKENING_SYSTEM -> Pair(PukaarColors.AccentAmber, "WEAKENING")
        CycloneStage.POST_TROPICAL_REMNANT -> Pair(PukaarColors.AccentGreen, "REMNANT")
    }

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(6.dp))
            .background(color.copy(alpha = 0.20f))
            .border(1.dp, color.copy(alpha = 0.80f), RoundedCornerShape(6.dp))
            .padding(horizontal = 8.dp, vertical = 2.dp)
    ) {
        Text(
            text = text,
            fontFamily = JetBrainsMonoFamily,
            fontSize = 10.sp,
            fontWeight = FontWeight.Bold,
            color = color
        )
    }
}

@Composable
private fun DataFreshnessPill(validUntil: String) {
    val freshness = evaluateFreshness(validUntil)
    val (bgColor, textColor, label) = when (freshness) {
        FreshnessState.VALID -> Triple(PukaarColors.AccentGreen.copy(alpha = 0.2f), PukaarColors.AccentGreen, "VALID")
        FreshnessState.STALE -> Triple(PukaarColors.AccentAmber.copy(alpha = 0.2f), PukaarColors.AccentAmber, "STALE")
        FreshnessState.EXPIRED -> Triple(PukaarColors.AccentRed.copy(alpha = 0.2f), PukaarColors.AccentRed, "EXPIRED")
    }

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(12.dp))
            .background(bgColor)
            .border(1.dp, textColor.copy(alpha = 0.6f), RoundedCornerShape(12.dp))
            .padding(horizontal = 10.dp, vertical = 3.dp)
    ) {
        Text(
            text = label,
            fontFamily = JetBrainsMonoFamily,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
            color = textColor
        )
    }
}

private enum class FreshnessState {
    VALID, STALE, EXPIRED
}

private fun evaluateFreshness(validUntil: String): FreshnessState {
    return try {
        val expiry = Instant.parse(validUntil).toEpochMilli()
        val now = System.currentTimeMillis()
        when {
            now <= expiry -> FreshnessState.VALID
            now - expiry < 3 * 3600 * 1000L -> FreshnessState.STALE
            else -> FreshnessState.EXPIRED
        }
    } catch (e: Exception) {
        FreshnessState.VALID
    }
}

private fun calculateOperationalConfidence(intelligence: CycloneIntelligence): Int {
    val freshnessWeight = if (evaluateFreshness(intelligence.validUntil) == FreshnessState.VALID) 1.0 else 0.5
    val operational = (intelligence.predictionConfidence * 0.7 + freshnessWeight * 0.3) * 100
    return operational.toInt().coerceIn(0, 100)
}

@Composable
private fun RadarScanOverlay(text: String) {
    val transition = rememberInfiniteTransition(label = "radar_sweep")
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
        Canvas(modifier = Modifier.size(280.dp)) {
            val center = Offset(size.width / 2f, size.height / 2f)
            val maxRadius = size.minDimension / 2f

            // Concentric rings
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

            // Cross grid lines
            drawLine(
                color = PukaarColors.AccentCyan.copy(alpha = 0.04f),
                start = Offset(center.x, center.y - maxRadius),
                end = Offset(center.x, center.y + maxRadius),
                strokeWidth = 1.dp.toPx()
            )
            drawLine(
                color = PukaarColors.AccentCyan.copy(alpha = 0.04f),
                start = Offset(center.x - maxRadius, center.y),
                end = Offset(center.x + maxRadius, center.y),
                strokeWidth = 1.dp.toPx()
            )

            // Sweeping arc
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
            modifier = Modifier.padding(top = 320.dp)
        ) {
            Text(
                text = text,
                fontFamily = RajdhaniFontFamily,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                letterSpacing = 2.sp,
                color = PukaarColors.AccentCyan
            )
        }
    }
}

private fun getRiskZoneStyle(riskLevel: RiskLevel): Triple<Color, Color, Float> {
    return when (riskLevel) {
        RiskLevel.EXTREME -> Triple(Color(0x20FF1744), Color(0xFFFF1744), 1.5f)
        RiskLevel.HIGH -> Triple(Color(0x18FF6D00), Color(0xFFFF6D00), 1.0f)
        RiskLevel.MODERATE -> Triple(Color(0x15FFD600), Color(0xFFFFD600), 1.0f)
        RiskLevel.LOW -> Triple(Color(0x1200E676), Color(0xFF00E676), 0.5f)
    }
}

private fun computeCentroid(points: List<MapLatLng>): MapLatLng {
    if (points.isEmpty()) return MapLatLng(0.0, 0.0)
    var latSum = 0.0
    var lngSum = 0.0
    for (pt in points) {
        latSum += pt.latitude
        lngSum += pt.longitude
    }
    return MapLatLng(latSum / points.size, lngSum / points.size)
}

private fun computeUncertaintyCone(path: List<PathPoint>, radiusKm: Double): List<MapLatLng> {
    if (path.isEmpty()) return emptyList()
    val degOffset = (radiusKm / 111.0).coerceAtLeast(0.1)

    val leftSide = mutableListOf<MapLatLng>()
    val rightSide = mutableListOf<MapLatLng>()

    for (i in path.indices) {
        val pt = path[i]
        val expansionFactor = 1.0 + (i.toDouble() / path.size) * 0.8
        val currentOffset = degOffset * expansionFactor

        leftSide.add(MapLatLng(pt.latitude + currentOffset, pt.longitude - currentOffset))
        rightSide.add(MapLatLng(pt.latitude - currentOffset, pt.longitude + currentOffset))
    }

    return leftSide + rightSide.reversed()
}

private fun createCrosshairBitmapDescriptor(context: Context, scale: Float = 1.0f): BitmapDescriptor {
    val density = context.resources.displayMetrics.density
    val sizePx = (48 * density).toInt()
    val bitmap = Bitmap.createBitmap(sizePx, sizePx, Bitmap.Config.ARGB_8888)
    val canvas = android.graphics.Canvas(bitmap)
    val paint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = android.graphics.Color.parseColor("#00D4FF")
    }
    val center = sizePx / 2f

    // Outer ring (24dp diameter * scale)
    paint.style = android.graphics.Paint.Style.STROKE
    paint.strokeWidth = 2 * density
    paint.alpha = (255 * (1f / scale)).coerceIn(50f, 255f).toInt()
    canvas.drawCircle(center, 12 * density * scale, paint)

    // Inner ring (14dp diameter)
    paint.strokeWidth = 1 * density
    paint.alpha = 255
    canvas.drawCircle(center, 7 * density, paint)

    // Cross lines N/S/E/W
    val crossLen = 6 * density
    canvas.drawLine(center, center - 7 * density, center, center - 7 * density - crossLen, paint)
    canvas.drawLine(center, center + 7 * density, center, center + 7 * density + crossLen, paint)
    canvas.drawLine(center - 7 * density, center, center - 7 * density - crossLen, center, paint)
    canvas.drawLine(center + 7 * density, center, center + 7 * density + crossLen, center, paint)

    // Center dot (4dp diameter)
    paint.style = android.graphics.Paint.Style.FILL
    canvas.drawCircle(center, 2 * density, paint)

    return BitmapDescriptorFactory.fromBitmap(bitmap)
}

private fun createArrowBitmapDescriptor(context: Context): BitmapDescriptor {
    val density = context.resources.displayMetrics.density
    val sizePx = (16 * density).toInt()
    val bitmap = Bitmap.createBitmap(sizePx, sizePx, Bitmap.Config.ARGB_8888)
    val canvas = android.graphics.Canvas(bitmap)
    val paint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = android.graphics.Color.parseColor("#00D4FF")
        style = android.graphics.Paint.Style.FILL
    }
    val path = android.graphics.Path().apply {
        moveTo(sizePx / 2f, 2 * density)
        lineTo(sizePx - 2 * density, sizePx - 2 * density)
        lineTo(sizePx / 2f, sizePx - 6 * density)
        lineTo(2 * density, sizePx - 2 * density)
        close()
    }
    canvas.drawPath(path, paint)
    return BitmapDescriptorFactory.fromBitmap(bitmap)
}

private fun createTextLabelBitmapDescriptor(context: Context, text: String, colorInt: Int): BitmapDescriptor {
    val density = context.resources.displayMetrics.density
    val paint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = colorInt
        textSize = 10 * density
        typeface = android.graphics.Typeface.DEFAULT_BOLD
    }
    val bounds = android.graphics.Rect()
    paint.getTextBounds(text, 0, text.length, bounds)
    val width = bounds.width() + (12 * density).toInt()
    val height = bounds.height() + (8 * density).toInt()

    val bitmap = Bitmap.createBitmap(width.coerceAtLeast(1), height.coerceAtLeast(1), Bitmap.Config.ARGB_8888)
    val canvas = android.graphics.Canvas(bitmap)

    val bgPaint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = android.graphics.Color.parseColor("#E6091525")
        style = android.graphics.Paint.Style.FILL
    }
    val borderPaint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = colorInt
        style = android.graphics.Paint.Style.STROKE
        strokeWidth = 1 * density
    }
    val rect = android.graphics.RectF(0f, 0f, width.toFloat(), height.toFloat())
    canvas.drawRoundRect(rect, 4 * density, 4 * density, bgPaint)
    canvas.drawRoundRect(rect, 4 * density, 4 * density, borderPaint)
    canvas.drawText(text, 6 * density, height / 2f + bounds.height() / 2f - 1, paint)

    return BitmapDescriptorFactory.fromBitmap(bitmap)
}
