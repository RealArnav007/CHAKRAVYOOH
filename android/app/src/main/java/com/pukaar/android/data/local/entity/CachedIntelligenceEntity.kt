package com.pukaar.android.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.pukaar.android.domain.model.CycloneIntelligence
import com.pukaar.android.domain.model.CycloneStage
import com.pukaar.android.domain.model.IntensityLevel
import com.pukaar.android.domain.model.LatLng
import com.pukaar.android.domain.model.PathPoint

@Entity(tableName = "cached_intelligence")
data class CachedIntelligenceEntity(
    @PrimaryKey val cycloneId: String,
    val timestamp: String,
    val detected: Boolean,
    val detectionConfidence: Double,
    val classificationStage: String,
    val classificationConfidence: Double,
    val intensityLevel: String,
    val intensityConfidence: Double,
    val currentLatitude: Double,
    val currentLongitude: Double,
    val heading: String,
    val forecastHours: Int,
    val predictionConfidence: Double,
    val predictedPathJson: String,
    val uncertaintyRadiusKm: Double,
    val generatedAt: String,
    val validUntil: String
) {
    fun toDomain(gson: Gson): CycloneIntelligence {
        val pathType = object : TypeToken<List<PathPoint>>() {}.type
        val path: List<PathPoint> = try {
            gson.fromJson(predictedPathJson, pathType) ?: emptyList()
        } catch (e: Exception) {
            emptyList()
        }

        val stage = try {
            CycloneStage.valueOf(classificationStage)
        } catch (e: Exception) {
            CycloneStage.DEVELOPING_DISTURBANCE
        }

        val intensity = try {
            IntensityLevel.valueOf(intensityLevel)
        } catch (e: Exception) {
            IntensityLevel.MODERATE
        }

        return CycloneIntelligence(
            cycloneId = cycloneId,
            timestamp = timestamp,
            detected = detected,
            detectionConfidence = detectionConfidence,
            classificationStage = stage,
            classificationConfidence = classificationConfidence,
            intensityLevel = intensity,
            intensityConfidence = intensityConfidence,
            currentPosition = LatLng(currentLatitude, currentLongitude),
            heading = heading,
            forecastHours = forecastHours,
            predictionConfidence = predictionConfidence,
            predictedPath = path,
            uncertaintyRadiusKm = uncertaintyRadiusKm,
            generatedAt = generatedAt,
            validUntil = validUntil
        )
    }

    companion object {
        fun fromDomain(domain: CycloneIntelligence, gson: Gson): CachedIntelligenceEntity {
            return CachedIntelligenceEntity(
                cycloneId = domain.cycloneId,
                timestamp = domain.timestamp,
                detected = domain.detected,
                detectionConfidence = domain.detectionConfidence,
                classificationStage = domain.classificationStage.name,
                classificationConfidence = domain.classificationConfidence,
                intensityLevel = domain.intensityLevel.name,
                intensityConfidence = domain.intensityConfidence,
                currentLatitude = domain.currentPosition.latitude,
                currentLongitude = domain.currentPosition.longitude,
                heading = domain.heading,
                forecastHours = domain.forecastHours,
                predictionConfidence = domain.predictionConfidence,
                predictedPathJson = gson.toJson(domain.predictedPath),
                uncertaintyRadiusKm = domain.uncertaintyRadiusKm,
                generatedAt = domain.generatedAt,
                validUntil = domain.validUntil
            )
        }
    }
}
