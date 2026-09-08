package com.pukaar.android.domain.usecase

import com.pukaar.android.domain.model.SosMessage
import com.pukaar.android.domain.repository.SosRepository
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow

class SendSosUseCase @Inject constructor(
    private val sosRepository: SosRepository
) {
    suspend operator fun invoke(
        latitude: Double,
        longitude: Double,
        emergencyType: String,
        victimCount: Int,
        notes: String
    ): Result<SosMessage> {
        return sosRepository.sendEmergencySos(latitude, longitude, emergencyType, victimCount, notes)
    }

    suspend fun cancel(sosId: String) = sosRepository.cancelSos(sosId)

    fun getActiveOutgoingSos(): Flow<SosMessage?> = sosRepository.getActiveOutgoingSosStream()
}
