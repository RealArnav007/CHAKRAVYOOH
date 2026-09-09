package com.pukaar.android.domain.repository

import com.pukaar.android.domain.model.RiskZone

interface RiskZoneRepository {
    suspend fun getRiskZones(): Result<List<RiskZone>>
}
