package com.pukaar.android.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.pukaar.android.domain.model.Alert
import com.pukaar.android.domain.model.RiskLevel

@Entity(tableName = "alerts")
data class AlertEntity(
    @PrimaryKey val id: String,
    val title: String,
    val description: String,
    val riskLevel: String,
    val category: String,
    val zone: String,
    val timestamp: Long,
    val expiresAt: Long,
    val actionAdvice: String,
    val isRead: Boolean,
    val isMeshRelayed: Boolean
) {
    fun toDomain(): Alert = Alert(
        id = id,
        title = title,
        description = description,
        riskLevel = RiskLevel.fromString(riskLevel),
        category = category,
        zone = zone,
        timestamp = timestamp,
        expiresAt = expiresAt,
        actionAdvice = actionAdvice,
        isRead = isRead,
        isMeshRelayed = isMeshRelayed
    )

    companion object {
        fun fromDomain(alert: Alert): AlertEntity = AlertEntity(
            id = alert.id,
            title = alert.title,
            description = alert.description,
            riskLevel = alert.riskLevel.name,
            category = alert.category,
            zone = alert.zone,
            timestamp = alert.timestamp,
            expiresAt = alert.expiresAt,
            actionAdvice = alert.actionAdvice,
            isRead = alert.isRead,
            isMeshRelayed = alert.isMeshRelayed
        )
    }
}
