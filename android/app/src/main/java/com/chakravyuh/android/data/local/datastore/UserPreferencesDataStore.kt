package com.chakravyuh.android.data.local.datastore

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.chakravyuh.android.domain.model.UserSettings
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "chakravyuh_user_prefs")

@Singleton
class UserPreferencesDataStore @Inject constructor(
    @ApplicationContext private val context: Context
) {
    companion object {
        val KEY_USER_ID = stringPreferencesKey("user_id")
        val KEY_USER_NAME = stringPreferencesKey("user_name")
        val KEY_EMERGENCY_CONTACT = stringPreferencesKey("emergency_contact")
        val KEY_BLOOD_GROUP = stringPreferencesKey("blood_group")
        val KEY_MESH_RELAY_ENABLED = booleanPreferencesKey("mesh_relay_enabled")
        val KEY_BT_SCANNING_ENABLED = booleanPreferencesKey("bt_scanning_enabled")
        val KEY_CRITICAL_AUDIO = booleanPreferencesKey("critical_audio")
        val KEY_OFFLINE_MAPS = booleanPreferencesKey("offline_maps")
        val KEY_SERVER_URL = stringPreferencesKey("server_url")
    }

    val userSettingsFlow: Flow<UserSettings> = context.dataStore.data.map { prefs ->
        UserSettings(
            userId = prefs[KEY_USER_ID] ?: "node_${System.currentTimeMillis() % 10000}",
            userName = prefs[KEY_USER_NAME] ?: "Citizen Responder",
            emergencyContactPhone = prefs[KEY_EMERGENCY_CONTACT] ?: "+91-112",
            bloodGroup = prefs[KEY_BLOOD_GROUP] ?: "O+",
            isMeshRelayEnabled = prefs[KEY_MESH_RELAY_ENABLED] ?: true,
            isBluetoothScanningEnabled = prefs[KEY_BT_SCANNING_ENABLED] ?: true,
            isCriticalAudioAlertEnabled = prefs[KEY_CRITICAL_AUDIO] ?: true,
            offlineMapCacheEnabled = prefs[KEY_OFFLINE_MAPS] ?: true,
            backendServerUrl = prefs[KEY_SERVER_URL] ?: "https://chakravyuh.live/api/v1"
        )
    }

    suspend fun saveSettings(settings: UserSettings) {
        context.dataStore.edit { prefs ->
            prefs[KEY_USER_ID] = settings.userId
            prefs[KEY_USER_NAME] = settings.userName
            prefs[KEY_EMERGENCY_CONTACT] = settings.emergencyContactPhone
            prefs[KEY_BLOOD_GROUP] = settings.bloodGroup
            prefs[KEY_MESH_RELAY_ENABLED] = settings.isMeshRelayEnabled
            prefs[KEY_BT_SCANNING_ENABLED] = settings.isBluetoothScanningEnabled
            prefs[KEY_CRITICAL_AUDIO] = settings.isCriticalAudioAlertEnabled
            prefs[KEY_OFFLINE_MAPS] = settings.offlineMapCacheEnabled
            prefs[KEY_SERVER_URL] = settings.backendServerUrl
        }
    }

    suspend fun setMeshRelayEnabled(enabled: Boolean) {
        context.dataStore.edit { prefs ->
            prefs[KEY_MESH_RELAY_ENABLED] = enabled
        }
    }
}
