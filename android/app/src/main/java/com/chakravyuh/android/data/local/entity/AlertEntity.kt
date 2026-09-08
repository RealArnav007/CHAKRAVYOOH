package com.chakravyuh.android.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.chakravyuh.android.domain.model.Alert
import com.chakravyuh.android.domain.model.ThreatLevel

@Entity(tableName = "alerts")
data class AlertEntity(
    @PrimaryKey
    val id: String,
    val title: String,
    val description: String,
    val threatLevel: String,
    val category: String,
    val zoneId: String,
    val affectedAreaName: String,
    val timestamp: Long,
    val expiresAt: Long,
    val actionAdvice: String,
    val isRead: Boolean,
    val isBroadcastingViaMesh: Boolean
) {
    fun toDomain(): Alert {
        return Alert(
            id = id,
            title = title,
            description = description,
            threatLevel = ThreatLevel.fromString(threatLevel),
            category = category,
            zoneId = zoneId,
            affectedAreaName = affectedAreaName,
            timestamp = timestamp,
            expiresAt = expiresAt,
            actionAdvice = actionAdvice,
            isRead = isRead,
            isBroadcastingViaMesh = isBroadcastingViaMesh
        )
    }

    companion object {
        fun fromDomain(alert: Alert): AlertEntity {
            return AlertEntity(
                id = alert.id,
                title = alert.title,
                description = alert.description,
                threatLevel = alert.threatLevel.name,
                category = alert.category,
                zoneId = alert.zoneId,
                affectedAreaName = alert.affectedAreaName,
                timestamp = alert.timestamp,
                expiresAt = alert.expiresAt,
                actionAdvice = alert.actionAdvice,
                isRead = alert.isRead,
                isBroadcastingViaMesh = alert.isBroadcastingViaMesh
            )
        }
    }
}
