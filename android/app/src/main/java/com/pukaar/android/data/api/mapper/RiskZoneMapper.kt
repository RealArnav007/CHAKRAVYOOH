package com.pukaar.android.data.api.mapper

import com.pukaar.android.data.api.dto.RiskZoneDto
import com.pukaar.android.domain.model.LatLng
import com.pukaar.android.domain.model.RiskLevel
import com.pukaar.android.domain.model.RiskZone

fun RiskZoneDto.toDomain(): RiskZone {
    val level = try {
        RiskLevel.valueOf(riskLevel.uppercase())
    } catch (e: Exception) {
        RiskLevel.LOW
    }

    val poly = polygon?.map {
        LatLng(latitude = it.latitude, longitude = it.longitude)
    } ?: emptyList()

    return RiskZone(
        zoneId = zoneId,
        zoneName = zoneName,
        riskLevel = level,
        polygon = poly
    )
}
