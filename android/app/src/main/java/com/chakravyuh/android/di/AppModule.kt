package com.chakravyuh.android.di

import com.chakravyuh.android.data.mesh.BluetoothMeshManagerImpl
import com.chakravyuh.android.data.mesh.MeshCryptoHelper
import com.chakravyuh.android.data.mesh.MeshNetworkManager
import com.google.gson.Gson
import com.google.gson.GsonBuilder
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
    fun provideGson(): Gson {
        return GsonBuilder()
            .setLenient()
            .create()
    }

    @Provides
    @Singleton
    fun provideMeshNetworkManager(
        impl: BluetoothMeshManagerImpl
    ): MeshNetworkManager = impl
}
