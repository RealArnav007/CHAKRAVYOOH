package com.chakravyuh.android.domain.usecase

import com.chakravyuh.android.domain.model.EvacuationRoute
import com.chakravyuh.android.domain.repository.EvacuationRepository
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow

class GetEvacuationRoutesUseCase @Inject constructor(
    private val evacuationRepository: EvacuationRepository
) {
    operator fun invoke(lat: Double, lon: Double): Flow<List<EvacuationRoute>> {
        return evacuationRepository.getSafeRoutesStream(lat, lon)
    }

    suspend fun refresh(lat: Double, lon: Double): Result<List<EvacuationRoute>> {
        return evacuationRepository.calculateEvacuationRoute(lat, lon)
    }
}
