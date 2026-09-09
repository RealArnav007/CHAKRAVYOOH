package com.pukaar.android.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.pukaar.android.domain.model.SosMessage
import com.pukaar.android.domain.model.SosStatus

@Entity(tableName = "sos_messages")
data class SosEntity(
    @PrimaryKey val id: String,
    val senderId: String,
    val senderName: String,
    val latitude: Double,
    val longitude: Double,
    val emergencyType: String,
    val victimCount: Int,
    val notes: String,
    val timestamp: Long,
    val hopCount: Int,
    val isEncrypted: Boolean,
    val signature: String,
    val status: String
) {
    fun toDomain(): SosMessage = SosMessage(
        id = id,
        senderId = senderId,
        senderName = senderName,
        latitude = latitude,
        longitude = longitude,
        emergencyType = emergencyType,
        victimCount = victimCount,
        notes = notes,
        timestamp = timestamp,
        hopCount = hopCount,
        isEncrypted = isEncrypted,
        signature = signature,
        status = try { SosStatus.valueOf(status) } catch (e: Exception) { SosStatus.QUEUED_FOR_MESH }
    )

    companion object {
        fun fromDomain(msg: SosMessage): SosEntity = SosEntity(
            id = msg.id,
            senderId = msg.senderId,
            senderName = msg.senderName,
            latitude = msg.latitude,
            longitude = msg.longitude,
            emergencyType = msg.emergencyType,
            victimCount = msg.victimCount,
            notes = msg.notes,
            timestamp = msg.timestamp,
            hopCount = msg.hopCount,
            isEncrypted = msg.isEncrypted,
            signature = msg.signature,
            status = msg.status.name
        )
    }
}
