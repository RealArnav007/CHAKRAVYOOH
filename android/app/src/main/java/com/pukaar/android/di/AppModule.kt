package com.pukaar.android.di

import com.google.gson.Gson
import com.google.gson.GsonBuilder
import com.pukaar.android.data.mesh.BluetoothLeMeshImpl
import com.pukaar.android.data.mesh.MeshManager
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideGson(): Gson = GsonBuilder().setLenient().create()

    @Provides
    @Singleton
    fun provideMeshManager(impl: BluetoothLeMeshImpl): MeshManager = impl
}
