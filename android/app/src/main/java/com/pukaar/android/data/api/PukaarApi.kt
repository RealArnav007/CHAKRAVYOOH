package com.pukaar.android.data.api

import com.pukaar.android.data.api.dto.CycloneAlertDto
import com.pukaar.android.data.api.dto.CycloneIntelligenceDto
import com.pukaar.android.data.api.dto.KeyRegistrationDto
import com.pukaar.android.data.api.dto.RiskZoneDto
import com.pukaar.android.data.api.dto.SosRequestDto
import com.pukaar.android.data.api.dto.SosResponseDto
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface PukaarApi {

    @GET("/cyclone/active")
    suspend fun getActiveCyclones(): List<CycloneIntelligenceDto>

    @GET("/cyclone/{id}")
    suspend fun getCycloneById(@Path("id") id: String): CycloneIntelligenceDto

    @GET("/cyclone/alerts")
    suspend fun getAlerts(): List<CycloneAlertDto>

    @GET("/zones/risk")
    suspend fun getRiskZones(): List<RiskZoneDto>

    @POST("/sos/ingest")
    suspend fun sendSos(@Body request: SosRequestDto): SosResponseDto

    @POST("/keys/register")
    suspend fun registerKey(@Body request: KeyRegistrationDto)
}
