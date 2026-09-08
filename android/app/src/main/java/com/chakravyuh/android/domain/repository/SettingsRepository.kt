package com.chakravyuh.android.domain.repository

import com.chakravyuh.android.domain.model.UserSettings
import kotlinx.coroutines.flow.Flow

interface SettingsRepository {
    fun getUserSettings(): Flow<UserSettings>
    suspend fun updateSettings(settings: UserSettings): Result<Unit>
    suspend fun setMeshRelayEnabled(enabled: Boolean)
}
