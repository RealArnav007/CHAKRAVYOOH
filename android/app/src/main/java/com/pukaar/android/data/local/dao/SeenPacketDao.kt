package com.pukaar.android.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.pukaar.android.data.local.entity.SeenPacketEntity

@Dao
interface SeenPacketDao {

    @Query("SELECT * FROM seen_packets WHERE msgId = :msgId LIMIT 1")
    suspend fun findById(msgId: String): SeenPacketEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(entity: SeenPacketEntity)

    @Query("DELETE FROM seen_packets WHERE seenAt < :timestamp")
    suspend fun deleteOlderThan(timestamp: Long)
}
