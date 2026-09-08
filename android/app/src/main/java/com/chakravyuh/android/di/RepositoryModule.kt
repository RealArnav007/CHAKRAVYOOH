package com.chakravyuh.android.di

import com.chakravyuh.android.data.repository.AlertRepositoryImpl
import com.chakravyuh.android.data.repository.CycloneRepositoryImpl
import com.chakravyuh.android.data.repository.EvacuationRepositoryImpl
import com.chakravyuh.android.data.repository.MeshRepositoryImpl
import com.chakravyuh.android.data.repository.SettingsRepositoryImpl
import com.chakravyuh.android.data.repository.SosRepositoryImpl
import com.chakravyuh.android.domain.repository.AlertRepository
import com.chakravyuh.android.domain.repository.CycloneRepository
import com.chakravyuh.android.domain.repository.EvacuationRepository
import com.chakravyuh.android.domain.repository.MeshRepository
import com.chakravyuh.android.domain.repository.SettingsRepository
import com.chakravyuh.android.domain.repository.SosRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindAlertRepository(impl: AlertRepositoryImpl): AlertRepository

    @Binds
    @Singleton
    abstract fun bindCycloneRepository(impl: CycloneRepositoryImpl): CycloneRepository

    @Binds
    @Singleton
    abstract fun bindEvacuationRepository(impl: EvacuationRepositoryImpl): EvacuationRepository

    @Binds
    @Singleton
    abstract fun bindMeshRepository(impl: MeshRepositoryImpl): MeshRepository

    @Binds
    @Singleton
    abstract fun bindSosRepository(impl: SosRepositoryImpl): SosRepository

    @Binds
    @Singleton
    abstract fun bindSettingsRepository(impl: SettingsRepositoryImpl): SettingsRepository
}
