package com.pukaar.android.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.pukaar.android.data.local.converters.PukaarTypeConverters
import com.pukaar.android.data.local.dao.AlertDao
import com.pukaar.android.data.local.dao.IncomingSosDao
import com.pukaar.android.data.local.dao.IntelligenceDao
import com.pukaar.android.data.local.dao.SeenPacketDao
import com.pukaar.android.data.local.entity.CachedAlertEntity
import com.pukaar.android.data.local.entity.CachedIntelligenceEntity
import com.pukaar.android.data.local.entity.IncomingSosEntity
import com.pukaar.android.data.local.entity.SeenPacketEntity

@Database(
    entities = [
        SeenPacketEntity::class,
        IncomingSosEntity::class,
        CachedAlertEntity::class,
        CachedIntelligenceEntity::class
    ],
    version = 1,
    exportSchema = false
)
@TypeConverters(PukaarTypeConverters::class)
abstract class PukaarDatabase : RoomDatabase() {
    abstract fun seenPacketDao(): SeenPacketDao
    abstract fun incomingSosDao(): IncomingSosDao
    abstract fun alertDao(): AlertDao
    abstract fun intelligenceDao(): IntelligenceDao
}
