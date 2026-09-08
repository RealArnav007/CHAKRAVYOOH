package com.chakravyuh.android.domain.usecase

import com.chakravyuh.android.domain.model.SosRequest
import com.chakravyuh.android.domain.repository.SosRepository
import javax.inject.Inject

class SendSosUseCase @Inject constructor(
    private val sosRepository: SosRepository
) {
    suspend operator fun invoke(
        latitude: Double,
        longitude: Double,
        emergencyType: String,
        victimCount: Int,
        notes: String
    ): Result<SosRequest> {
        return sosRepository.triggerSos(latitude, longitude, emergencyType, victimCount, notes)
    }

    suspend fun cancel(sosId: String): Result<Unit> {
        return sosRepository.cancelSos(sosId)
    }
}
