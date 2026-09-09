package com.pukaar.android.data.api.mapper

import com.pukaar.android.data.api.dto.CycloneIntelligenceDto
import com.pukaar.android.domain.model.CycloneIntelligence
import com.pukaar.android.domain.model.CycloneStage
import com.pukaar.android.domain.model.IntensityLevel
import com.pukaar.android.domain.model.LatLng
import com.pukaar.android.domain.model.PathPoint

fun CycloneIntelligenceDto.toDomain(): CycloneIntelligence {
    val stageEnum = try {
        CycloneStage.valueOf(classification?.stage ?: "DEVELOPING_DISTURBANCE")
    } catch (e: Exception) {
        CycloneStage.DEVELOPING_DISTURBANCE
    }

    val intensityEnum = try {
        IntensityLevel.valueOf(intensity?.level ?: "MODERATE")
    } catch (e: Exception) {
        IntensityLevel.MODERATE
    }

    val path = prediction?.predictedPath?.map {
        PathPoint(
            forecastHour = it.forecastHour,
            latitude = it.latitude,
            longitude = it.longitude
        )
    } ?: emptyList()

    val currentPos = currentPosition?.let {
        LatLng(latitude = it.latitude, longitude = it.longitude)
    } ?: LatLng(latitude = 0.0, longitude = 0.0)

    return CycloneIntelligence(
        cycloneId = cycloneId,
        timestamp = timestamp,
        detected = detected,
        detectionConfidence = detectionConfidence,
        classificationStage = stageEnum,
        classificationConfidence = classification?.confidence ?: 0.0,
        intensityLevel = intensityEnum,
        intensityConfidence = intensity?.confidence ?: 0.0,
        currentPosition = currentPos,
        heading = heading ?: "NNW",
        forecastHours = prediction?.forecastHours ?: 72,
        predictionConfidence = prediction?.confidence ?: 0.0,
        predictedPath = path,
        uncertaintyRadiusKm = uncertainty?.radiusKm ?: 45.0,
        generatedAt = freshness?.generatedAt ?: timestamp,
        validUntil = freshness?.validUntil ?: timestamp
    )
}
