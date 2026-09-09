package com.pukaar.android.data.repository

import com.google.gson.Gson
import com.pukaar.android.data.api.PukaarApi
import com.pukaar.android.data.api.mapper.toDomain
import com.pukaar.android.data.local.dao.IntelligenceDao
import com.pukaar.android.data.local.entity.CachedIntelligenceEntity
import com.pukaar.android.data.websocket.PukaarWebSocketManager
import com.pukaar.android.domain.model.CycloneIntelligence
import com.pukaar.android.domain.repository.CycloneEvent
import com.pukaar.android.domain.repository.CycloneRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CycloneRepositoryImpl @Inject constructor(
    private val api: PukaarApi,
    private val intelligenceDao: IntelligenceDao,
    private val wsManager: PukaarWebSocketManager,
    private val gson: Gson
) : CycloneRepository {

    override suspend fun getActiveCyclones(): Result<List<CycloneIntelligence>> {
        return try {
            val dtos = api.getActiveCyclones()
            val domainList = dtos.map { it.toDomain() }
            intelligenceDao.insertAll(domainList.map { CachedIntelligenceEntity.fromDomain(it, gson) })
            Result.success(domainList)
        } catch (e: Exception) {
            try {
                val cached = intelligenceDao.findById("active")
                if (cached != null) {
                    Result.success(listOf(cached.toDomain(gson)))
                } else {
                    Result.failure(e)
                }
            } catch (fallbackEx: Exception) {
                Result.failure(e)
            }
        }
    }

    override suspend fun getCycloneById(id: String): Result<CycloneIntelligence> {
        return try {
            val dto = api.getCycloneById(id)
            val domain = dto.toDomain()
            intelligenceDao.upsert(CachedIntelligenceEntity.fromDomain(domain, gson))
            Result.success(domain)
        } catch (e: Exception) {
            try {
                val cached = intelligenceDao.findById(id)
                if (cached != null) {
                    Result.success(cached.toDomain(gson))
                } else {
                    Result.failure(e)
                }
            } catch (fallbackEx: Exception) {
                Result.failure(e)
            }
        }
    }

    override fun observeCycloneEvents(): Flow<CycloneEvent> {
        return wsManager.eventsFlow
    }
}
