package com.chakravyuh.android.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.chakravyuh.android.data.local.entity.MeshMessageEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface MeshMessageDao {
    @Query("SELECT * FROM mesh_messages ORDER BY timestamp DESC")
    fun getAllMessages(): Flow<List<MeshMessageEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMessage(message: MeshMessageEntity)

    @Query("SELECT EXISTS(SELECT 1 FROM mesh_messages WHERE messageId = :messageId)")
    suspend fun exists(messageId: String): Boolean
}
