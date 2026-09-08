package com.chakravyuh.android.data.repository

import com.chakravyuh.android.domain.model.EvacuationRoute
import com.chakravyuh.android.domain.repository.EvacuationRepository
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

@Singleton
class EvacuationRepositoryImpl @Inject constructor() : EvacuationRepository {

    override fun getSafeRoutesStream(currentLat: Double, currentLon: Double): Flow<List<EvacuationRoute>> = flow {
        emit(getMockRoutes(currentLat, currentLon))
    }

    override suspend fun calculateEvacuationRoute(
        originLat: Double,
        originLon: Double
    ): Result<List<EvacuationRoute>> {
        return Result.success(getMockRoutes(originLat, originLon))
    }

    private fun getMockRoutes(lat: Double, lon: Double): List<EvacuationRoute> {
        return listOf(
            EvacuationRoute(
                routeId = "ROUTE_SEC_01",
                destinationName = "Sector 9 Concrete Cyclone Haven",
                shelterCapacity = 1450,
                distanceKm = 4.2,
                estimatedMinutes = 14,
                safetyScore = 0.96,
                waypoints = listOf(
                    Pair(lat, lon),
                    Pair(lat + 0.015, lon - 0.010),
                    Pair(lat + 0.030, lon - 0.022),
                    Pair(lat + 0.045, lon - 0.035)
                ),
                roadConditions = "Elevated bypass clear of floodwaters. Reinforced barrier.",
                recommendedTransport = "VEHICLE"
            ),
            EvacuationRoute(
                routeId = "ROUTE_SEC_02",
                destinationName = "High School Emergency Relief Point",
                shelterCapacity = 800,
                distanceKm = 2.1,
                estimatedMinutes = 25,
                safetyScore = 0.88,
                waypoints = listOf(
                    Pair(lat, lon),
                    Pair(lat + 0.008, lon + 0.005),
                    Pair(lat + 0.018, lon + 0.012)
                ),
                roadConditions = "Pedestrian corridor open. Moderate wind exposure.",
                recommendedTransport = "FOOT"
            ),
            EvacuationRoute(
                routeId = "ROUTE_SEC_03",
                destinationName = "District Multi-purpose Disaster Shelter",
                shelterCapacity = 3200,
                distanceKm = 8.7,
                estimatedMinutes = 22,
                safetyScore = 0.99,
                waypoints = listOf(
                    Pair(lat, lon),
                    Pair(lat + 0.020, lon - 0.030),
                    Pair(lat + 0.055, lon - 0.065),
                    Pair(lat + 0.080, lon - 0.090)
                ),
                roadConditions = "Main National Highway green corridor with emergency generator backup.",
                recommendedTransport = "VEHICLE"
            )
        )
    }
}
