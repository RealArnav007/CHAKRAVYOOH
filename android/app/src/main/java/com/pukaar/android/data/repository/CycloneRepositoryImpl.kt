package com.pukaar.android.data.repository

import com.google.gson.Gson
import com.pukaar.android.data.api.PukaarApiService
import com.pukaar.android.data.demo.DemoDataGenerator
import com.pukaar.android.data.local.dao.CycloneDao
import com.pukaar.android.data.local.entity.CycloneEntity
import com.pukaar.android.domain.model.CycloneData
import com.pukaar.android.domain.repository.CycloneRepository
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

@Singleton
class CycloneRepositoryImpl @Inject constructor(
    private val cycloneDao: CycloneDao,
    private val apiService: PukaarApiService,
    private val gson: Gson
) : CycloneRepository {

    override fun getCycloneStream(): Flow<CycloneData?> {
        return cycloneDao.getLatestCyclone().map { entity ->
            entity?.toDomain(gson) ?: DemoDataGenerator.generateCyclone()
        }
    }

    override suspend fun refreshCycloneData(): Result<CycloneData> {
        return try {
            val res = apiService.getActiveCyclone()
            if (res.isSuccessful && res.body() != null) {
                val domain = res.body()!!.toDomain()
                cycloneDao.insertCyclone(CycloneEntity.fromDomain(domain, gson))
                Result.success(domain)
            } else {
                val demo = DemoDataGenerator.generateCyclone()
                cycloneDao.insertCyclone(CycloneEntity.fromDomain(demo, gson))
                Result.success(demo)
            }
        } catch (e: Exception) {
            val demo = DemoDataGenerator.generateCyclone()
            cycloneDao.insertCyclone(CycloneEntity.fromDomain(demo, gson))
            Result.success(demo)
        }
    }
}
