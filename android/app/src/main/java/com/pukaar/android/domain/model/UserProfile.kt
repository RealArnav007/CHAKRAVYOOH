package com.pukaar.android.domain.model

data class UserProfile(
    val userId: String,
    val name: String,
    val phone: String,
    val bloodGroup: String,
    val isMeshRelayEnabled: Boolean = true,
    val isOnboardingComplete: Boolean = false,
    val criticalSirenEnabled: Boolean = true
)
