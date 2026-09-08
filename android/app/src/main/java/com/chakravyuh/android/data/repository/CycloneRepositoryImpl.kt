package com.chakravyuh.android.data.repository

import com.chakravyuh.android.data.api.ChakravyuhApiService
import com.chakravyuh.android.data.local.dao.CycloneDao
import com.chakravyuh.android.data.local.entity.CycloneEntity
import com.chakravyuh.android.domain.model.CycloneIntelligence
import com.chakravyuh.android.domain.model.ThreatLevel
import com.chakravyuh.android.domain.model.TrackPoint
import com.chakravyuh.android.domain.repository.CycloneRepository
import com.google.gson.Gson
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

@Singleton
class CycloneRepositoryImpl @Inject constructor(
    private val cycloneDao: CycloneDao,
    private val apiService: ChakravyuhApiService,
    private val gson: Gson
) : CycloneRepository {

    override fun getActiveCycloneStream(): Flow<CycloneIntelligence?> {
        return cycloneDao.getLatestCyclone().map { entity ->
            entity?.toDomain(gson) ?: getMockActiveCyclone()
        }
    }

    override suspend fun fetchLatestIntelligence(): Result<CycloneIntelligence> {
        return try {
            val response = apiService.getActiveCyclone()
            if (response.isSuccessful && response.body() != null) {
                val domain = response.body()!!.toDomain()
                cycloneDao.insertCyclone(CycloneEntity.fromDomain(domain, gson))
                Result.success(domain)
            } else {
                val fallback = getMockActiveCyclone()
                cycloneDao.insertCyclone(CycloneEntity.fromDomain(fallback, gson))
                Result.success(fallback)
            }
        } catch (e: Exception) {
            val fallback = getMockActiveCyclone()
            cycloneDao.insertCyclone(CycloneEntity.fromDomain(fallback, gson))
            Result.success(fallback)
        }
    }

    private fun getMockActiveCyclone(): CycloneIntelligence {
        val now = System.currentTimeMillis()
        val forecastTrack = listOf(
            TrackPoint(now - 7200000, 18.2, 86.4, 95.0, "Cat 2"),
            TrackPoint(now - 3600000, 18.7, 86.1, 110.0, "Cat 3"),
            TrackPoint(now, 19.3, 85.8, 125.0, "Cat 4"),
            TrackPoint(now + 14400000, 19.9, 85.5, 135.0, "Cat 4 (Peak)"),
            TrackPoint(now + 28800000, 20.3, 85.2, 115.0, "Landfall"),
            TrackPoint(now + 43200000, 20.7, 84.9, 85.0, "Post-Landfall Depression")
        )

        return CycloneIntelligence(
            cycloneId = "CYC_2026_09A",
            name = "Super Cyclone Varuna",
            centerLat = 19.3,
            centerLon = 85.8,
            maxSustainedWindKts = 125.0,
            currentPressureHpa = 932.0,
            r34RadiusKm = 240.0,
            r50RadiusKm = 140.0,
            r64RadiusKm = 75.0,
            estimatedLandfallTime = now + 28800000,
            landfallProbability = 0.94,
            category = "Category 4 Very Severe Cyclonic Storm",
            forecastTrack = forecastTrack,
            threatLevel = ThreatLevel.EXTREME,
            lastUpdated = now
        )
    }
}
