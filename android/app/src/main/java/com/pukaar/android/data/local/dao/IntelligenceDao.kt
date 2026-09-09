package com.pukaar.android.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.pukaar.android.data.local.entity.CachedIntelligenceEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface IntelligenceDao {
    @Query("SELECT * FROM cached_intelligence ORDER BY timestamp DESC LIMIT 1")
    fun getLatestAsFlow(): Flow<CachedIntelligenceEntity?>

    @Query("SELECT * FROM cached_intelligence WHERE cycloneId = :cycloneId LIMIT 1")
    suspend fun findById(cycloneId: String): CachedIntelligenceEntity?

    @Query("SELECT * FROM cached_intelligence ORDER BY timestamp DESC")
    fun getAllAsFlow(): Flow<List<CachedIntelligenceEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(intelligence: CachedIntelligenceEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(list: List<CachedIntelligenceEntity>)

    @Query("DELETE FROM cached_intelligence WHERE cycloneId = :cycloneId")
    suspend fun deleteById(cycloneId: String)
}
