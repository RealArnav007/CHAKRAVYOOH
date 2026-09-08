package com.pukaar.android.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "seen_packets")
data class SeenPacketEntity(
    @PrimaryKey val msgId: String,
    val seenAt: Long
)
