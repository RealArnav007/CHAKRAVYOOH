package com.pukaar.android.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.pukaar.android.data.local.entity.MeshPeerEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface MeshPeerDao {
    @Query("SELECT * FROM mesh_peers ORDER BY lastSeenTimestamp DESC")
    fun getAllPeers(): Flow<List<MeshPeerEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPeers(peers: List<MeshPeerEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPeer(peer: MeshPeerEntity)
}
