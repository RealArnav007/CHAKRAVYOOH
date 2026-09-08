package com.chakravyuh.android.domain.model

/**
 * User configuration and mesh relay preferences.
 */
data class UserSettings(
    val userId: String,
    val userName: String,
    val emergencyContactPhone: String,
    val bloodGroup: String,
    val isMeshRelayEnabled: Boolean = true,
    val isBluetoothScanningEnabled: Boolean = true,
    val isCriticalAudioAlertEnabled: Boolean = true,
    val offlineMapCacheEnabled: Boolean = true,
    val backendServerUrl: String = "https://chakravyuh.live/api/v1"
)
