package com.chakravyuh.android.ui.screens.map

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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DirectionsRun
import androidx.compose.material.icons.filled.Layers
import androidx.compose.material.icons.filled.Navigation
import androidx.compose.material.icons.filled.Radar
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.chakravyuh.android.ui.components.ChakravyuhTopBar
import com.chakravyuh.android.ui.components.PulsingBeacon
import com.chakravyuh.android.ui.theme.ChakravyuhBackground
import com.chakravyuh.android.ui.theme.ChakravyuhOutline
import com.chakravyuh.android.ui.theme.ChakravyuhPrimary
import com.chakravyuh.android.ui.theme.ChakravyuhSurface
import com.chakravyuh.android.ui.theme.ThreatExtreme
import com.chakravyuh.android.ui.theme.ThreatHigh
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

@Composable
fun MapScreen(
    onNavigateToSettings: () -> Unit,
    viewModel: MapViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsState()
    val cycloneCenter = LatLng(
        state.cyclone?.centerLat ?: 19.3,
        state.cyclone?.centerLon ?: 85.8
    )
    val userPosition = LatLng(state.userLatitude, state.userLongitude)

    val cameraPositionState = rememberCameraPositionState {
        position = CameraPosition.fromLatLngZoom(userPosition, 8f)
    }

    var activeLayer by remember { mutableStateOf(MapLayer.ALL) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(ChakravyuhBackground)
    ) {
        ChakravyuhTopBar(
            title = "Geospatial Radar",
            threatLevel = state.cyclone?.threatLevel ?: ThreatExtreme,
            onSettingsClick = onNavigateToSettings
        )

        Box(modifier = Modifier.fillMaxSize()) {
            GoogleMap(
                modifier = Modifier.fillMaxSize(),
                cameraPositionState = cameraPositionState,
                properties = MapProperties(
                    mapType = MapType.NORMAL,
                    isTrafficEnabled = false
                ),
                uiSettings = MapUiSettings(
                    zoomControlsEnabled = false,
                    compassEnabled = true
                )
            ) {
                // User Location Marker
                Marker(
                    state = MarkerState(position = userPosition),
                    title = "Your Location",
                    snippet = "Puri Coastal District (Risk: HIGH)"
                )

                // Cyclone Eye Marker & Radii
                Marker(
                    state = MarkerState(position = cycloneCenter),
                    title = state.cyclone?.name ?: "Cyclone Eye",
                    snippet = "Sustained: ${state.cyclone?.maxSustainedWindKts?.toInt() ?: 125} kts"
                )

                // R64 Extreme Wind Radius (Red)
                Circle(
                    center = cycloneCenter,
                    radius = (state.cyclone?.r64RadiusKm ?: 75.0) * 1000,
                    fillColor = ThreatExtreme.copy(alpha = 0.25f),
                    strokeColor = ThreatExtreme,
                    strokeWidth = 3f
                )

                // R50 Destructive Radius (Orange)
                Circle(
                    center = cycloneCenter,
                    radius = (state.cyclone?.r50RadiusKm ?: 140.0) * 1000,
                    fillColor = ThreatHigh.copy(alpha = 0.15f),
                    strokeColor = ThreatHigh,
                    strokeWidth = 2f
                )

                // Forecast Track Polyline
                val trackLatLngs = state.cyclone?.forecastTrack?.map {
                    LatLng(it.latitude, it.longitude)
                } ?: emptyList()

                if (trackLatLngs.isNotEmpty()) {
                    Polyline(
                        points = trackLatLngs,
                        color = ThreatExtreme,
                        width = 6f
                    )
                }

                // Evacuation Route Polylines
                state.routes.forEach { route ->
                    val routePoints = route.waypoints.map { LatLng(it.first, it.second) }
                    Polyline(
                        points = routePoints,
                        color = ChakravyuhPrimary,
                        width = 8f
                    )
                    if (routePoints.isNotEmpty()) {
                        Marker(
                            state = MarkerState(position = routePoints.last()),
                            title = route.destinationName,
                            snippet = "Capacity: ${route.shelterCapacity} | Safety: ${(route.safetyScore * 100).toInt()}%"
                        )
                    }
                }
            }

            // Tactical Overlay HUD
            Column(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Card(
                    colors = CardDefaults.cardColors(containerColor = ChakravyuhSurface.copy(alpha = 0.95f)),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, ChakravyuhOutline, RoundedCornerShape(12.dp))
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(14.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(
                                text = "PRIMARY EVACUATION CORRIDOR",
                                style = MaterialTheme.typography.labelSmall,
                                color = ChakravyuhPrimary
                            )
                            Spacer(modifier = Modifier.height(2.dp))
                            Text(
                                text = state.routes.firstOrNull()?.destinationName ?: "Haven Sector 9",
                                style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                                color = MaterialTheme.colorScheme.onBackground
                            )
                            Text(
                                text = "ETA: ${state.routes.firstOrNull()?.estimatedMinutes ?: 14} min • Safety: 96%",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }

                        IconButton(
                            onClick = {},
                            modifier = Modifier
                                .clip(RoundedCornerShape(8.dp))
                                .background(ChakravyuhPrimary)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Navigation,
                                contentDescription = "Start Navigation",
                                tint = Color.White
                            )
                        }
                    }
                }
            }
        }
    }
}
