package com.pukaar.android.data.repository

import com.pukaar.android.data.local.UserPreferences
import com.pukaar.android.domain.model.UserProfile
import com.pukaar.android.domain.repository.UserRepository
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow

@Singleton
class UserRepositoryImpl @Inject constructor(
    private val userPreferences: UserPreferences
) : UserRepository {

    override fun getUserProfile(): Flow<UserProfile> {
        return userPreferences.userProfile
    }

    override suspend fun saveProfile(profile: UserProfile): Result<Unit> {
        userPreferences.saveProfile(profile)
        return Result.success(Unit)
    }

    override suspend fun setOnboardingComplete(complete: Boolean) {
        userPreferences.setOnboardingComplete(complete)
    }
}
