package com.pukaar.android.domain.model

data class CycloneData(
    val cycloneId: String,
    val name: String,
    val centerLat: Double,
    val centerLon: Double,
    val currentWindSpeedKts: Double,
    val centralPressureHpa: Double,
    val r34Km: Double,
    val r50Km: Double,
    val r64Km: Double,
    val landfallEtaTimestamp: Long,
    val landfallProbability: Double,
    val category: String,
    val riskLevel: RiskLevel,
    val trajectory: List<CyclonePoint>,
    val safetyEvacuationPath: List<Pair<Double, Double>>,
    val lastUpdated: Long
)

data class CyclonePoint(
    val timestamp: Long,
    val latitude: Double,
    val longitude: Double,
    val windKts: Double,
    val label: String
)
