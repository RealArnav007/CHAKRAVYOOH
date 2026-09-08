package com.pukaar.android.di

import com.pukaar.android.data.repository.AlertRepositoryImpl
import com.pukaar.android.data.repository.CycloneRepositoryImpl
import com.pukaar.android.data.repository.MeshRepositoryImpl
import com.pukaar.android.data.repository.SosRepositoryImpl
import com.pukaar.android.data.repository.UserRepositoryImpl
import com.pukaar.android.domain.repository.AlertRepository
import com.pukaar.android.domain.repository.CycloneRepository
import com.pukaar.android.domain.repository.MeshRepository
import com.pukaar.android.domain.repository.SosRepository
import com.pukaar.android.domain.repository.UserRepository
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
    abstract fun bindSosRepository(impl: SosRepositoryImpl): SosRepository

    @Binds
    @Singleton
    abstract fun bindMeshRepository(impl: MeshRepositoryImpl): MeshRepository

    @Binds
    @Singleton
    abstract fun bindUserRepository(impl: UserRepositoryImpl): UserRepository
}
