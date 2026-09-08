package com.pukaar.android.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import com.pukaar.android.data.local.dao.AlertDao
import com.pukaar.android.data.local.dao.CycloneDao
import com.pukaar.android.data.local.dao.MeshPeerDao
import com.pukaar.android.data.local.dao.SosDao
import com.pukaar.android.data.local.entity.AlertEntity
import com.pukaar.android.data.local.entity.CycloneEntity
import com.pukaar.android.data.local.entity.MeshPeerEntity
import com.pukaar.android.data.local.entity.SosEntity

@Database(
    entities = [
        AlertEntity::class,
        CycloneEntity::class,
        SosEntity::class,
        MeshPeerEntity::class
    ],
    version = 1,
    exportSchema = false
)
abstract class PukaarDatabase : RoomDatabase() {
    abstract fun alertDao(): AlertDao
    abstract fun cycloneDao(): CycloneDao
    abstract fun sosDao(): SosDao
    abstract fun meshPeerDao(): MeshPeerDao
}
