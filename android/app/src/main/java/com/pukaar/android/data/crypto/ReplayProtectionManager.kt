package com.pukaar.android.data.crypto

import com.pukaar.android.data.local.dao.SeenPacketDao
import com.pukaar.android.data.local.entity.SeenPacketEntity
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ReplayProtectionManager @Inject constructor(
    private val seenPacketDao: SeenPacketDao
) {
    suspend fun isDuplicate(msgId: String): Boolean {
        return seenPacketDao.findById(msgId) != null
    }

    suspend fun markSeen(msgId: String) {
        seenPacketDao.insert(SeenPacketEntity(msgId, System.currentTimeMillis()))
    }

    suspend fun pruneOldPackets(maxAgeMillis: Long = TimeUnit.HOURS.toMillis(24)) {
        val cutoff = System.currentTimeMillis() - maxAgeMillis
        seenPacketDao.deleteOlderThan(cutoff)
    }
}
