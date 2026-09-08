package com.pukaar.android.data.repository

import com.pukaar.android.data.api.PukaarApi
import com.pukaar.android.data.api.mapper.toDomain
import com.pukaar.android.domain.model.RiskZone
import com.pukaar.android.domain.repository.RiskZoneRepository
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class RiskZoneRepositoryImpl @Inject constructor(
    private val api: PukaarApi
) : RiskZoneRepository {

    override suspend fun getRiskZones(): Result<List<RiskZone>> {
        return try {
            val dtos = api.getRiskZones()
            Result.success(dtos.map { it.toDomain() })
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
