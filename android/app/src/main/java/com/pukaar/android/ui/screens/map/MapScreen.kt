package com.pukaar.android.ui.screens.map

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Navigation
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.google.android.gms.maps.model.CameraPosition
import com.google.android.gms.maps.model.LatLng
import com.google.maps.android.compose.Circle
import com.google.maps.android.compose.GoogleMap
import com.google.maps.android.compose.MapProperties
import com.google.maps.android.compose.MapType
import com.google.maps.android.compose.MapUiSettings
import com.google.maps.android.compose.Marker
import com.google.maps.android.compose.MarkerState
import com.google.maps.android.compose.Polyline
import com.google.maps.android.compose.rememberCameraPositionState
import com.pukaar.android.ui.components.GlowCard
import com.pukaar.android.ui.components.RiskBadge
import com.pukaar.android.ui.components.StatusDot
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily

@Composable
fun MapScreen(
    onNavigateToSettings: () -> Unit,
    viewModel: MapViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val cyclone = state.cyclone

    val centerLatLng = LatLng(cyclone?.centerLat ?: 19.3, cyclone?.centerLon ?: 85.8)
    val userLatLng = LatLng(state.userLat, state.userLon)

    val cameraPositionState = rememberCameraPositionState {
        position = CameraPosition.fromLatLngZoom(userLatLng, 8f)
    }

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
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                StatusDot(color = PukaarColors.AccentCyan)
                Text(
                    text = "GEOSPATIAL RADAR",
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 22.sp,
                    letterSpacing = 1.5.sp,
                    color = PukaarColors.TextPrimary
                )
            }

            IconButton(onClick = onNavigateToSettings) {
                Icon(
                    imageVector = Icons.Default.Settings,
                    contentDescription = "Settings",
                    tint = PukaarColors.TextSecondary
                )
            }
        }

        Box(modifier = Modifier.fillMaxSize()) {
            GoogleMap(
                modifier = Modifier.fillMaxSize(),
                cameraPositionState = cameraPositionState,
                properties = MapProperties(mapType = MapType.NORMAL),
                uiSettings = MapUiSettings(zoomControlsEnabled = false, compassEnabled = true)
            ) {
                // User Location
                Marker(
                    state = MarkerState(position = userLatLng),
                    title = "Your Location",
                    snippet = "Puri Coastal Sector"
                )

                // Cyclone Center
                Marker(
                    state = MarkerState(position = centerLatLng),
                    title = cyclone?.name ?: "Cyclone Eye",
                    snippet = "Wind: ${cyclone?.currentWindSpeedKts?.toInt() ?: 125} kts"
                )

                // R64 Radius (Red)
                Circle(
                    center = centerLatLng,
                    radius = (cyclone?.r64Km ?: 75.0) * 1000,
                    fillColor = PukaarColors.AccentRed.copy(alpha = 0.25f),
                    strokeColor = PukaarColors.AccentRed,
                    strokeWidth = 3f
                )

                // R50 Radius (Amber)
                Circle(
                    center = centerLatLng,
                    radius = (cyclone?.r50Km ?: 140.0) * 1000,
                    fillColor = PukaarColors.AccentAmber.copy(alpha = 0.15f),
                    strokeColor = PukaarColors.AccentAmber,
                    strokeWidth = 2f
                )

                // Forecast Track
                val trackPoints = cyclone?.trajectory?.map { LatLng(it.latitude, it.longitude) } ?: emptyList()
                if (trackPoints.isNotEmpty()) {
                    Polyline(points = trackPoints, color = PukaarColors.AccentRed, width = 6f)
                }

                // Evacuation Path
                val evacPoints = cyclone?.safetyEvacuationPath?.map { LatLng(it.first, it.second) } ?: emptyList()
                if (evacPoints.isNotEmpty()) {
                    Polyline(points = evacPoints, color = PukaarColors.AccentCyan, width = 8f)
                    Marker(
                        state = MarkerState(position = evacPoints.last()),
                        title = "Shelter Alpha",
                        snippet = "Reinforced Safe Haven"
                    )
                }
            }

            // Floating Tactical Overlay HUD
            Column(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(16.dp)
            ) {
                GlowCard(
                    glowColor = PukaarColors.AccentCyan,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(
                                text = "CALCULATED SAFE CORRIDOR",
                                style = MaterialTheme.typography.labelSmall,
                                color = PukaarColors.AccentCyan
                            )
                            Spacer(modifier = Modifier.height(2.dp))
                            Text(
                                text = "Reinforced Cyclone Haven #9",
                                fontFamily = RajdhaniFontFamily,
                                fontWeight = FontWeight.Bold,
                                fontSize = 18.sp,
                                color = PukaarColors.TextPrimary
                            )
                            Text(
                                text = "ETA: 14 min • Surge Barrier Clear",
                                style = MaterialTheme.typography.bodySmall,
                                color = PukaarColors.TextSecondary
                            )
                        }

                        Button(
                            onClick = {},
                            colors = ButtonDefaults.buttonColors(containerColor = PukaarColors.AccentCyan),
                            modifier = Modifier.clip(RoundedCornerShape(8.dp))
                        ) {
                            Icon(imageVector = Icons.Default.Navigation, contentDescription = null, tint = PukaarColors.BgVoid)
                        }
                    }
                }
            }
        }
    }
}
