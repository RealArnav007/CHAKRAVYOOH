package com.pukaar.android.domain.usecase

import com.pukaar.android.domain.model.SosMessage
import com.pukaar.android.domain.repository.SosRepository
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow

class GetSosInboxUseCase @Inject constructor(
    private val sosRepository: SosRepository
) {
    operator fun invoke(): Flow<List<SosMessage>> = sosRepository.getSosInboxStream()
}
