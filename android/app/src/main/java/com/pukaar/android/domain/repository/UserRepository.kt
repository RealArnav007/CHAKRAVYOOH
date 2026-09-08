package com.pukaar.android.domain.repository

import com.pukaar.android.domain.model.UserProfile
import kotlinx.coroutines.flow.Flow

interface UserRepository {
    fun getUserProfile(): Flow<UserProfile>
    suspend fun saveProfile(profile: UserProfile): Result<Unit>
    suspend fun setOnboardingComplete(complete: Boolean)
}
