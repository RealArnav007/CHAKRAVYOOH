package com.pukaar.android.data.repository

import com.pukaar.android.data.api.PukaarApi
import com.pukaar.android.data.api.mapper.toDto
import com.pukaar.android.data.local.dao.IncomingSosDao
import com.pukaar.android.data.local.entity.IncomingSosEntity
import com.pukaar.android.domain.model.IncomingSos
import com.pukaar.android.domain.model.RelayStatus
import com.pukaar.android.domain.model.SosRequest
import com.pukaar.android.domain.repository.SosRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SosRepositoryImpl @Inject constructor(
    private val api: PukaarApi,
    private val incomingSosDao: IncomingSosDao
) : SosRepository {

    override suspend fun sendSos(request: SosRequest): Result<String> {
        return try {
            val response = api.sendSos(request.toDto())
            Result.success(response.sosId)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override fun observeIncomingSos(): Flow<List<IncomingSos>> {
        return incomingSosDao.getAllAsFlow().map { list ->
            list.map { it.toDomain() }
        }
    }

    override suspend fun getInboxSnapshot(): List<IncomingSos> {
        return incomingSosDao.getAll().map { it.toDomain() }
    }

    override suspend fun updateRelayStatus(msgId: String, status: RelayStatus) {
        incomingSosDao.updateRelayStatus(msgId, status.name)
    }
}
