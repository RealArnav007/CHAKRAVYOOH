package com.chakravyuh.android.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.chakravyuh.android.data.local.entity.CycloneEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface CycloneDao {
    @Query("SELECT * FROM cyclone_intelligence ORDER BY lastUpdated DESC LIMIT 1")
    fun getLatestCyclone(): Flow<CycloneEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCyclone(cyclone: CycloneEntity)

    @Query("DELETE FROM cyclone_intelligence")
    suspend fun clear()
}
