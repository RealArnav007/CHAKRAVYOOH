package com.pukaar.android.di

import android.content.Context
import androidx.room.Room
import com.pukaar.android.data.local.PukaarDatabase
import com.pukaar.android.data.local.dao.AlertDao
import com.pukaar.android.data.local.dao.IncomingSosDao
import com.pukaar.android.data.local.dao.IntelligenceDao
import com.pukaar.android.data.local.dao.SeenPacketDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): PukaarDatabase {
        return Room.databaseBuilder(
            context,
            PukaarDatabase::class.java,
            "pukaar.db"
        )
        .fallbackToDestructiveMigration()
        .build()
    }

    @Provides
    fun provideSeenPacketDao(db: PukaarDatabase): SeenPacketDao = db.seenPacketDao()

    @Provides
    fun provideIncomingSosDao(db: PukaarDatabase): IncomingSosDao = db.incomingSosDao()

    @Provides
    fun provideAlertDao(db: PukaarDatabase): AlertDao = db.alertDao()

    @Provides
    fun provideIntelligenceDao(db: PukaarDatabase): IntelligenceDao = db.intelligenceDao()
}
