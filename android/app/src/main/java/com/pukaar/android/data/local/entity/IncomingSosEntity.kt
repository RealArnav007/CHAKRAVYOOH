package com.pukaar.android.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.pukaar.android.domain.model.EmergencyType
import com.pukaar.android.domain.model.IncomingSos
import com.pukaar.android.domain.model.MeshTransport
import com.pukaar.android.domain.model.RelayStatus
import com.pukaar.android.domain.model.VerificationStatus

@Entity(tableName = "incoming_sos")
data class IncomingSosEntity(
    @PrimaryKey val msgId: String,
    val senderHash: String,
    val emergencyType: String,
    val latitude: Double?,
    val longitude: Double?,
    val message: String?,
    val receivedAt: Long,
    val hopCount: Int,
    val transport: String,
    val relayStatus: String,
    val verificationStatus: String
) {
    fun toDomain(): IncomingSos {
        val type = try {
            EmergencyType.valueOf(emergencyType)
        } catch (e: Exception) {
            EmergencyType.OTHER
        }

        val trans = try {
            MeshTransport.valueOf(transport)
        } catch (e: Exception) {
            MeshTransport.BLUETOOTH
        }

        val relay = try {
            RelayStatus.valueOf(relayStatus)
        } catch (e: Exception) {
            RelayStatus.PENDING
        }

        val verification = try {
            VerificationStatus.valueOf(verificationStatus)
        } catch (e: Exception) {
            VerificationStatus.PENDING
        }

        return IncomingSos(
            msgId = msgId,
            senderHash = senderHash,
            emergencyType = type,
            latitude = latitude,
            longitude = longitude,
            message = message,
            receivedAt = receivedAt,
            hopCount = hopCount,
            transport = trans,
            relayStatus = relay,
            verificationStatus = verification
        )
    }

    companion object {
        fun fromDomain(model: IncomingSos): IncomingSosEntity = IncomingSosEntity(
            msgId = model.msgId,
            senderHash = model.senderHash,
            emergencyType = model.emergencyType.name,
            latitude = model.latitude,
            longitude = model.longitude,
            message = model.message,
            receivedAt = model.receivedAt,
            hopCount = model.hopCount,
            transport = model.transport.name,
            relayStatus = model.relayStatus.name,
            verificationStatus = model.verificationStatus.name
        )
    }
}
