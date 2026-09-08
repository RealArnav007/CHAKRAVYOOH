package com.chakravyuh.android.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import com.chakravyuh.android.data.local.dao.AlertDao
import com.chakravyuh.android.data.local.dao.CycloneDao
import com.chakravyuh.android.data.local.dao.MeshMessageDao
import com.chakravyuh.android.data.local.entity.AlertEntity
import com.chakravyuh.android.data.local.entity.CycloneEntity
import com.chakravyuh.android.data.local.entity.MeshMessageEntity

@Database(
    entities = [
        AlertEntity::class,
        CycloneEntity::class,
        MeshMessageEntity::class
    ],
    version = 1,
    exportSchema = false
)
abstract class ChakravyuhDatabase : RoomDatabase() {
    abstract fun alertDao(): AlertDao
    abstract fun cycloneDao(): CycloneDao
    abstract fun meshMessageDao(): MeshMessageDao
}
