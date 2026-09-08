package com.pukaar.android.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.pukaar.android.domain.model.UserProfile
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.pukaarDataStore: DataStore<Preferences> by preferencesDataStore(name = "pukaar_user_prefs")

@Singleton
class UserPreferences @Inject constructor(
    @ApplicationContext private val context: Context
) {
    companion object {
        val KEY_USER_ID = stringPreferencesKey("pukaar_user_id")
        val KEY_USER_NAME = stringPreferencesKey("pukaar_user_name")
        val KEY_PHONE = stringPreferencesKey("pukaar_phone")
        val KEY_BLOOD_GROUP = stringPreferencesKey("pukaar_blood_group")
        val KEY_MESH_RELAY = booleanPreferencesKey("pukaar_mesh_relay")
        val KEY_ONBOARDING_DONE = booleanPreferencesKey("pukaar_onboarding_done")
        val KEY_CRITICAL_SIREN = booleanPreferencesKey("pukaar_critical_siren")
    }

    val userProfile: Flow<UserProfile> = context.pukaarDataStore.data.map { prefs ->
        UserProfile(
            userId = prefs[KEY_USER_ID] ?: "node_${System.currentTimeMillis() % 10000}",
            name = prefs[KEY_USER_NAME] ?: "Citizen Responder",
            phone = prefs[KEY_PHONE] ?: "+91-112",
            bloodGroup = prefs[KEY_BLOOD_GROUP] ?: "O+",
            isMeshRelayEnabled = prefs[KEY_MESH_RELAY] ?: true,
            isOnboardingComplete = prefs[KEY_ONBOARDING_DONE] ?: false,
            criticalSirenEnabled = prefs[KEY_CRITICAL_SIREN] ?: true
        )
    }

    suspend fun saveProfile(profile: UserProfile) {
        context.pukaarDataStore.edit { prefs ->
            prefs[KEY_USER_ID] = profile.userId
            prefs[KEY_USER_NAME] = profile.name
            prefs[KEY_PHONE] = profile.phone
            prefs[KEY_BLOOD_GROUP] = profile.bloodGroup
            prefs[KEY_MESH_RELAY] = profile.isMeshRelayEnabled
            prefs[KEY_ONBOARDING_DONE] = profile.isOnboardingComplete
            prefs[KEY_CRITICAL_SIREN] = profile.criticalSirenEnabled
        }
    }

    suspend fun setOnboardingComplete(complete: Boolean) {
        context.pukaarDataStore.edit { prefs ->
            prefs[KEY_ONBOARDING_DONE] = complete
        }
    }

    suspend fun setMeshRelayEnabled(enabled: Boolean) {
        context.pukaarDataStore.edit { prefs ->
            prefs[KEY_MESH_RELAY] = enabled
        }
    }
}
