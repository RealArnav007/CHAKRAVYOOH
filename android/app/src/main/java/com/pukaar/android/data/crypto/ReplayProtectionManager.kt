package com.pukaar.android.data.crypto

// NEVER log: private key bytes, signature bytes in full, decrypted SOS payload content, sender PII
// Safe to log: msgId (truncated), packet type, verification result (VERIFIED/INVALID), timestamp

import com.pukaar.android.data.local.dao.SeenPacketDao
import com.pukaar.android.data.local.entity.SeenPacketEntity
import com.pukaar.android.domain.model.MeshPacket
import java.time.Instant
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.abs

@Singleton
class ReplayProtectionManager @Inject constructor(
    private val seenPacketDao: SeenPacketDao
) {

    private val MAX_CLOCK_SKEW_MS = 5 * 60 * 1000L

    suspend fun isDuplicate(packet: MeshPacket): Boolean {
        if (seenPacketDao.findById(packet.msgId) != null) return true
        // Check timestamp skew
        val age = try {
            abs(System.currentTimeMillis() - Instant.parse(packet.createdAt).toEpochMilli())
        } catch (e: Exception) {
            Long.MAX_VALUE
        }
        if (age > MAX_CLOCK_SKEW_MS && age < 365 * 24 * 3600 * 1000L) return true
        seenPacketDao.insert(SeenPacketEntity(packet.msgId, System.currentTimeMillis()))
        return false
    }

    suspend fun isDuplicate(msgId: String): Boolean {
        return seenPacketDao.findById(msgId) != null
    }

    suspend fun markSeen(msgId: String) {
        seenPacketDao.insert(SeenPacketEntity(msgId, System.currentTimeMillis()))
    }

    fun enforceTTL(packet: MeshPacket): MeshPacket? =
        if (packet.ttl <= 0) null else packet.copy(ttl = packet.ttl - 1, hops = packet.hops + 1)

    suspend fun cleanOldEntries() {
        // Delete seen packets older than 24h (prevents DB bloat)
        val cutoff = System.currentTimeMillis() - 24 * 60 * 60 * 1000L
        seenPacketDao.deleteOlderThan(cutoff)
    }
}
