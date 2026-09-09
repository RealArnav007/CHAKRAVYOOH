package com.pukaar.android.data.api

import com.pukaar.android.data.api.dto.AlertDto
import com.pukaar.android.data.api.dto.CycloneDto
import com.pukaar.android.data.api.dto.SosDispatchDto
import com.pukaar.android.data.api.dto.SosStatusResponseDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Query

interface PukaarApiService {

    @GET("cyclone/active")
    suspend fun getActiveCyclone(): Response<CycloneDto>

    @GET("alerts")
    suspend fun getAlerts(
        @Query("lat") lat: Double? = null,
        @Query("lon") lon: Double? = null
    ): Response<List<AlertDto>>

    @POST("sos/dispatch")
    suspend fun dispatchSos(
        @Body payload: SosDispatchDto
    ): Response<SosStatusResponseDto>
}
