package com.pukaar.android.domain.repository

import com.pukaar.android.domain.model.IncomingSos
import com.pukaar.android.domain.model.RelayStatus
import com.pukaar.android.domain.model.SosRequest
import kotlinx.coroutines.flow.Flow

interface SosRepository {
    suspend fun sendSos(request: SosRequest): Result<String>
    fun observeIncomingSos(): Flow<List<IncomingSos>>
    suspend fun getInboxSnapshot(): List<IncomingSos>
    suspend fun updateRelayStatus(msgId: String, status: RelayStatus)
}
