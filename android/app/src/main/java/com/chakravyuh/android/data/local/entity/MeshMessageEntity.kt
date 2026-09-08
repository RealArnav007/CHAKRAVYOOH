package com.chakravyuh.android.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.chakravyuh.android.domain.model.MeshMessage

@Entity(tableName = "mesh_messages")
data class MeshMessageEntity(
    @PrimaryKey
    val messageId: String,
    val senderNodeId: String,
    val recipientNodeId: String?,
    val payload: String,
    val signatureHex: String,
    val timestamp: Long,
    val hopLimit: Int,
    val hopsTraversed: Int,
    val isEmergencySos: Boolean,
    val isDelivered: Boolean
) {
    fun toDomain(): MeshMessage {
        return MeshMessage(
            messageId = messageId,
            senderNodeId = senderNodeId,
            recipientNodeId = recipientNodeId,
            payload = payload,
            signatureHex = signatureHex,
            timestamp = timestamp,
            hopLimit = hopLimit,
            hopsTraversed = hopsTraversed,
            isEmergencySos = isEmergencySos,
            isDelivered = isDelivered
        )
    }

    companion object {
        fun fromDomain(model: MeshMessage): MeshMessageEntity {
            return MeshMessageEntity(
                messageId = model.messageId,
                senderNodeId = model.senderNodeId,
                recipientNodeId = model.recipientNodeId,
                payload = model.payload,
                signatureHex = model.signatureHex,
                timestamp = model.timestamp,
                hopLimit = model.hopLimit,
                hopsTraversed = model.hopsTraversed,
                isEmergencySos = model.isEmergencySos,
                isDelivered = model.isDelivered
            )
        }
    }
}
