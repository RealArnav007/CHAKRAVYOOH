package com.chakravyuh.android.data.repository

import com.chakravyuh.android.data.local.datastore.UserPreferencesDataStore
import com.chakravyuh.android.domain.model.UserSettings
import com.chakravyuh.android.domain.repository.SettingsRepository
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow

@Singleton
class SettingsRepositoryImpl @Inject constructor(
    private val preferencesDataStore: UserPreferencesDataStore
) : SettingsRepository {

    override fun getUserSettings(): Flow<UserSettings> {
        return preferencesDataStore.userSettingsFlow
    }

    override suspend fun updateSettings(settings: UserSettings): Result<Unit> {
        preferencesDataStore.saveSettings(settings)
        return Result.success(Unit)
    }

    override suspend fun setMeshRelayEnabled(enabled: Boolean) {
        preferencesDataStore.setMeshRelayEnabled(enabled)
    }
}
