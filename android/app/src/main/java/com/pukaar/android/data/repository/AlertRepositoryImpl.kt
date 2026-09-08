package com.pukaar.android.data.repository

import com.google.gson.Gson
import com.pukaar.android.data.api.PukaarApi
import com.pukaar.android.data.api.mapper.toDomain
import com.pukaar.android.data.local.dao.AlertDao
import com.pukaar.android.data.local.entity.CachedAlertEntity
import com.pukaar.android.domain.model.CycloneAlert
import com.pukaar.android.domain.repository.AlertRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AlertRepositoryImpl @Inject constructor(
    private val api: PukaarApi,
    private val alertDao: AlertDao,
    private val gson: Gson
) : AlertRepository {

    private val _alertEvents = MutableSharedFlow<CycloneAlert>(replay = 0, extraBufferCapacity = 64)

    override suspend fun getAlerts(): Result<List<CycloneAlert>> {
        return try {
            val dtos = api.getAlerts()
            val domainList = dtos.map { it.toDomain() }
            alertDao.insertAll(domainList.map { CachedAlertEntity.fromDomain(it, gson) })
            Result.success(domainList)
        } catch (e: Exception) {
            try {
                val cached = alertDao.getAll()
                if (cached.isNotEmpty()) {
                    Result.success(cached.map { it.toDomain(gson) })
                } else {
                    Result.failure(e)
                }
            } catch (fallbackEx: Exception) {
                Result.failure(e)
            }
        }
    }

    override fun observeAlertEvents(): Flow<CycloneAlert> {
        return _alertEvents.asSharedFlow()
    }

    suspend fun emitAlert(alert: CycloneAlert) {
        _alertEvents.emit(alert)
    }
}
