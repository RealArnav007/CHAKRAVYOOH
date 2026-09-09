package com.pukaar.android.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.pukaar.android.domain.model.CycloneAlert
import com.pukaar.android.domain.model.RiskLevel
import com.pukaar.android.domain.model.VerificationStatus

@Entity(tableName = "cached_alerts")
data class CachedAlertEntity(
    @PrimaryKey val alertId: String,
    val version: Int,
    val issuedAt: String,
    val updatedAt: String,
    val validUntil: String,
    val supersedes: String?,
    val riskLevel: String,
    val message: String,
    val affectedZonesJson: String,
    val signature: String,
    val verificationStatus: String
) {
    fun toDomain(gson: Gson): CycloneAlert {
        val listType = object : TypeToken<List<String>>() {}.type
        val zones: List<String> = try {
            gson.fromJson(affectedZonesJson, listType) ?: emptyList()
        } catch (e: Exception) {
            emptyList()
        }

        val level = try {
            RiskLevel.valueOf(riskLevel)
        } catch (e: Exception) {
            RiskLevel.MODERATE
        }

        val status = try {
            VerificationStatus.valueOf(verificationStatus)
        } catch (e: Exception) {
            VerificationStatus.PENDING
        }

        return CycloneAlert(
            alertId = alertId,
            version = version,
            issuedAt = issuedAt,
            updatedAt = updatedAt,
            validUntil = validUntil,
            supersedes = supersedes,
            riskLevel = level,
            message = message,
            affectedZones = zones,
            signature = signature,
            verificationStatus = status
        )
    }

    companion object {
        fun fromDomain(domain: CycloneAlert, gson: Gson): CachedAlertEntity {
            return CachedAlertEntity(
                alertId = domain.alertId,
                version = domain.version,
                issuedAt = domain.issuedAt,
                updatedAt = domain.updatedAt,
                validUntil = domain.validUntil,
                supersedes = domain.supersedes,
                riskLevel = domain.riskLevel.name,
                message = domain.message,
                affectedZonesJson = gson.toJson(domain.affectedZones),
                signature = domain.signature,
                verificationStatus = domain.verificationStatus.name
            )
        }
    }
}
