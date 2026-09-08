package com.pukaar.android.data.repository

import com.pukaar.android.data.api.PukaarApiService
import com.pukaar.android.data.demo.DemoDataGenerator
import com.pukaar.android.data.local.dao.AlertDao
import com.pukaar.android.data.local.entity.AlertEntity
import com.pukaar.android.domain.model.Alert
import com.pukaar.android.domain.repository.AlertRepository
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

@Singleton
class AlertRepositoryImpl @Inject constructor(
    private val alertDao: AlertDao,
    private val apiService: PukaarApiService
) : AlertRepository {

    override fun getAlertsStream(): Flow<List<Alert>> {
        return alertDao.getAllAlerts().map { list ->
            if (list.isEmpty()) {
                val demo = DemoDataGenerator.generateAlerts()
                demo
            } else {
                list.map { it.toDomain() }
            }
        }
    }

    override suspend fun refreshAlerts(): Result<Unit> {
        return try {
            val res = apiService.getAlerts()
            if (res.isSuccessful && res.body() != null) {
                val dtoList = res.body()!!
                alertDao.insertAlerts(dtoList.map { AlertEntity.fromDomain(it.toDomain()) })
            } else {
                alertDao.insertAlerts(DemoDataGenerator.generateAlerts().map { AlertEntity.fromDomain(it) })
            }
            Result.success(Unit)
        } catch (e: Exception) {
            alertDao.insertAlerts(DemoDataGenerator.generateAlerts().map { AlertEntity.fromDomain(it) })
            Result.success(Unit)
        }
    }

    override suspend fun markAlertAsRead(alertId: String) {
        alertDao.markAsRead(alertId)
    }
}
