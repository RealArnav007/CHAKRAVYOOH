package com.pukaar.android.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.pukaar.android.data.local.entity.CachedAlertEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface AlertDao {

    @Query("SELECT * FROM cached_alerts ORDER BY issuedAt DESC")
    fun getAllAsFlow(): Flow<List<CachedAlertEntity>>

    @Query("SELECT * FROM cached_alerts ORDER BY issuedAt DESC")
    suspend fun getAll(): List<CachedAlertEntity>

    @Query("SELECT * FROM cached_alerts WHERE alertId = :alertId LIMIT 1")
    suspend fun findById(alertId: String): CachedAlertEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(alert: CachedAlertEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(alerts: List<CachedAlertEntity>)

    @Query("DELETE FROM cached_alerts WHERE alertId = :alertId")
    suspend fun deleteById(alertId: String)
}
