package com.pukaar.android.data.mesh

import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.media.RingtoneManager
import androidx.core.app.NotificationCompat
import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.pukaar.android.MainActivity
import com.pukaar.android.data.local.dao.IncomingSosDao
import com.pukaar.android.data.local.dao.SeenPacketDao
import com.pukaar.android.data.local.entity.IncomingSosEntity
import com.pukaar.android.data.local.entity.SeenPacketEntity
import com.pukaar.android.data.repository.MeshRepositoryImpl
import com.pukaar.android.domain.model.EmergencyType
import com.pukaar.android.domain.model.MeshPacket
import com.pukaar.android.domain.model.MeshTransport
import com.pukaar.android.domain.model.MessageType
import com.pukaar.android.domain.model.PacketLogEntry
import com.pukaar.android.domain.model.PacketLogStatus
import com.pukaar.android.domain.model.RelayStatus
import com.pukaar.android.domain.model.VerificationStatus
import com.pukaar.android.domain.repository.MeshRepository
import com.pukaar.android.service.MeshReceiverService
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.security.MessageDigest
import java.time.Instant
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class MeshPacketProcessor @Inject constructor(
    private val seenPacketDao: SeenPacketDao,
    private val incomingSosDao: IncomingSosDao,
    private val meshRepository: MeshRepository,
    private val alertVerificationService: AlertVerificationService,
    @ApplicationContext private val context: Context
) {

    private val gson = Gson()
    private val _packetLog = MutableStateFlow<List<PacketLogEntry>>(emptyList())
    val packetLog: StateFlow<List<PacketLogEntry>> = _packetLog.asStateFlow()

    suspend fun process(packet: MeshPacket, transport: MeshTransport) {

        // STEP 1: Replay check
        val isDuplicate = seenPacketDao.findById(packet.msgId) != null
        if (isDuplicate) {
            log(packet, PacketLogStatus.DROPPED_DUPLICATE, transport)
            return
        }
        seenPacketDao.insert(SeenPacketEntity(packet.msgId, System.currentTimeMillis()))

        // STEP 2: Timestamp / clock skew check
        val packetAge = System.currentTimeMillis() - parseEpoch(packet.createdAt)
        if (packetAge > 5 * 60 * 1000L && packetAge < 365 * 24 * 3600 * 1000L) {  // 5 minute max age (if valid recent format)
            log(packet, PacketLogStatus.DROPPED_INVALID_SIG, transport)
            return
        }

        // STEP 3: TTL check
        if (packet.ttl <= 0) {
            log(packet, PacketLogStatus.DROPPED_TTL, transport)
            return
        }

        // STEP 4: Signature verification (verify sender identity)
        val sigValid = verifySenderSignature(packet)
        val verificationStatus = if (sigValid) VerificationStatus.VERIFIED else VerificationStatus.UNVERIFIED

        // STEP 5: Handle by type
        when (packet.messageType) {
            MessageType.SOS -> handleIncomingSos(packet, transport, verificationStatus)
            MessageType.CYCLONE_WARNING -> handleCycloneWarning(packet, verificationStatus)
            else -> { /* informational — just log */ }
        }

        // STEP 6: Relay (decrement TTL, increment hops)
        val relayPacket = packet.copy(ttl = packet.ttl - 1, hops = packet.hops + 1)
        val relayResult = meshRepository.relayPacket(relayPacket)
        log(packet, if (relayResult.isSuccess) PacketLogStatus.RELAYED else PacketLogStatus.DROPPED_INVALID_SIG, transport)
    }

    private suspend fun handleIncomingSos(packet: MeshPacket, transport: MeshTransport, verification: VerificationStatus) {
        val decoded = decodesSosPayload(packet.encryptedPayload)
        val senderHash = sha256hex(packet.senderIdentity).take(8)

        val incoming = IncomingSosEntity(
            msgId = packet.msgId,
            senderHash = senderHash,
            emergencyType = decoded.type.name,
            latitude = decoded.latitude,
            longitude = decoded.longitude,
            message = decoded.message,
            receivedAt = System.currentTimeMillis(),
            hopCount = packet.hops,
            transport = transport.name,
            relayStatus = RelayStatus.PENDING.name,
            verificationStatus = verification.name
        )

        incomingSosDao.insertOrReplace(incoming)
        postSosNotification(incoming)
        log(packet, PacketLogStatus.RECEIVED, transport)
    }

    private fun handleCycloneWarning(packet: MeshPacket, verification: VerificationStatus) {
        // Can be routed to alert cache or notification
    }

    private fun postSosNotification(sos: IncomingSosEntity) {
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager ?: return

        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("NAV_DESTINATION", "sos_inbox")
            putExtra("SOS_MSG_ID", sos.msgId)
        }

        val pendingIntent = PendingIntent.getActivity(
            context,
            sos.msgId.hashCode(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val alarmSound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
            ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)

        val notification = NotificationCompat.Builder(context, MeshReceiverService.SOS_NOTIFICATION_CHANNEL_ID)
            .setSmallIcon(android.R.drawable.stat_notify_error)
            .setContentTitle("⚠ SOS RECEIVED — ${sos.emergencyType}")
            .setContentText("From relay ${sos.senderHash} via mesh. Tap to view.")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setVibrate(longArrayOf(0, 500, 200, 500))
            .setSound(alarmSound)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()

        notificationManager.notify(sos.msgId.hashCode(), notification)
    }

    private fun log(packet: MeshPacket, status: PacketLogStatus, transport: MeshTransport) {
        val entry = PacketLogEntry(
            msgId = packet.msgId.take(8) + "...",  // truncated for privacy
            type = packet.messageType,
            timestamp = System.currentTimeMillis(),
            status = status,
            transport = transport
        )
        val updated = listOf(entry) + _packetLog.value.take(49)
        _packetLog.value = updated

        // Also update meshRepository log if it's the MeshRepositoryImpl
        (meshRepository as? MeshRepositoryImpl)?.addPacketLogEntry(entry)
    }

    private fun verifySenderSignature(packet: MeshPacket): Boolean {
        return alertVerificationService.verifyPayloadSignature(packet.encryptedPayload, packet.signature, packet.senderIdentity)
    }

    private fun decodesSosPayload(payload: String): SosPayloadDecoded {
        return try {
            val json: JsonObject = JsonParser.parseString(payload).asJsonObject
            val typeStr = json.get("emergency_type")?.asString ?: json.get("type")?.asString ?: "OTHER"
            val emergencyType = try { EmergencyType.valueOf(typeStr) } catch (e: Exception) { EmergencyType.OTHER }
            val lat = json.get("latitude")?.asDouble
            val lng = json.get("longitude")?.asDouble
            val msg = json.get("message")?.asString
            SosPayloadDecoded(emergencyType, lat, lng, msg)
        } catch (e: Exception) {
            SosPayloadDecoded(EmergencyType.OTHER, null, null, null)
        }
    }

    private fun sha256hex(input: String): String {
        return try {
            val digest = MessageDigest.getInstance("SHA-256").digest(input.toByteArray(Charsets.UTF_8))
            digest.joinToString("") { "%02x".format(it) }
        } catch (e: Exception) {
            input.hashCode().toString()
        }
    }

    private fun parseEpoch(timestamp: String): Long {
        return try {
            Instant.parse(timestamp).toEpochMilli()
        } catch (e: Exception) {
            try {
                timestamp.toLong()
            } catch (ex: Exception) {
                System.currentTimeMillis()
            }
        }
    }

    data class SosPayloadDecoded(
        val type: EmergencyType,
        val latitude: Double?,
        val longitude: Double?,
        val message: String?
    )
}
