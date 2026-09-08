package com.chakravyuh.android.domain.usecase

import com.chakravyuh.android.domain.model.CycloneIntelligence
import com.chakravyuh.android.domain.repository.CycloneRepository
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow

class GetCycloneIntelligenceUseCase @Inject constructor(
    private val cycloneRepository: CycloneRepository
) {
    operator fun invoke(): Flow<CycloneIntelligence?> {
        return cycloneRepository.getActiveCycloneStream()
    }

    suspend fun refresh(): Result<CycloneIntelligence> {
        return cycloneRepository.fetchLatestIntelligence()
    }
}
