package com.pukaar.android.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.pukaar.android.data.local.entity.SosEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface SosDao {
    @Query("SELECT * FROM sos_messages ORDER BY timestamp DESC")
    fun getAllSosMessages(): Flow<List<SosEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSos(sos: SosEntity)

    @Query("SELECT * FROM sos_messages WHERE id = :id")
    suspend fun getSosById(id: String): SosEntity?
}
