package com.pukaar.android.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.pukaar.android.data.local.entity.IncomingSosEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface IncomingSosDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrReplace(entity: IncomingSosEntity)

    @Query("SELECT * FROM incoming_sos ORDER BY receivedAt DESC")
    fun getAllAsFlow(): Flow<List<IncomingSosEntity>>

    @Query("SELECT * FROM incoming_sos ORDER BY receivedAt DESC")
    suspend fun getAll(): List<IncomingSosEntity>

    @Query("SELECT * FROM incoming_sos WHERE msgId = :msgId LIMIT 1")
    suspend fun findById(msgId: String): IncomingSosEntity?

    @Query("UPDATE incoming_sos SET relayStatus = :status WHERE msgId = :msgId")
    suspend fun updateRelayStatus(msgId: String, status: String)
}
