package com.pukaar.android.di

import android.content.Context
import androidx.room.Room
import com.pukaar.android.data.local.PukaarDatabase
import com.pukaar.android.data.local.dao.AlertDao
import com.pukaar.android.data.local.dao.CycloneDao
import com.pukaar.android.data.local.dao.MeshPeerDao
import com.pukaar.android.data.local.dao.SosDao
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
    fun provideAlertDao(db: PukaarDatabase): AlertDao = db.alertDao()

    @Provides
    fun provideCycloneDao(db: PukaarDatabase): CycloneDao = db.cycloneDao()

    @Provides
    fun provideSosDao(db: PukaarDatabase): SosDao = db.sosDao()

    @Provides
    fun provideMeshPeerDao(db: PukaarDatabase): MeshPeerDao = db.meshPeerDao()
}
