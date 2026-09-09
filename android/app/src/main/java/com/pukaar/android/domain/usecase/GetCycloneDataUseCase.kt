package com.pukaar.android.domain.usecase

import com.pukaar.android.domain.model.CycloneData
import com.pukaar.android.domain.repository.CycloneRepository
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow

class GetCycloneDataUseCase @Inject constructor(
    private val cycloneRepository: CycloneRepository
) {
    operator fun invoke(): Flow<CycloneData?> = cycloneRepository.getCycloneStream()

    suspend fun refresh(): Result<CycloneData> = cycloneRepository.refreshCycloneData()
}
