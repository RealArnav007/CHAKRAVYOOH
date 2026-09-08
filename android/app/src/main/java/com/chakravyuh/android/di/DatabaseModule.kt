package com.chakravyuh.android.di

import android.content.Context
import androidx.room.Room
import com.chakravyuh.android.data.local.ChakravyuhDatabase
import com.chakravyuh.android.data.local.dao.AlertDao
import com.chakravyuh.android.data.local.dao.CycloneDao
import com.chakravyuh.android.data.local.dao.MeshMessageDao
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
    fun provideDatabase(@ApplicationContext context: Context): ChakravyuhDatabase {
        return Room.databaseBuilder(
            context,
            ChakravyuhDatabase::class.java,
            "chakravyuh.db"
        )
        .fallbackToDestructiveMigration()
        .build()
    }

    @Provides
    fun provideAlertDao(database: ChakravyuhDatabase): AlertDao = database.alertDao()

    @Provides
    fun provideCycloneDao(database: ChakravyuhDatabase): CycloneDao = database.cycloneDao()

    @Provides
    fun provideMeshMessageDao(database: ChakravyuhDatabase): MeshMessageDao = database.meshMessageDao()
}
