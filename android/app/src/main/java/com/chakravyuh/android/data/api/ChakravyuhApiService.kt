package com.chakravyuh.android.data.api

import com.chakravyuh.android.data.api.dto.AlertDto
import com.chakravyuh.android.data.api.dto.CycloneDto
import com.chakravyuh.android.data.api.dto.SosPayloadDto
import com.chakravyuh.android.data.api.dto.SosResponseDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface ChakravyuhApiService {

    @GET("cyclone/active")
    suspend fun getActiveCyclone(): Response<CycloneDto>

    @GET("alerts")
    suspend fun getAlerts(
        @Query("lat") lat: Double? = null,
        @Query("lon") lon: Double? = null,
        @Query("radius_km") radiusKm: Double? = null
    ): Response<List<AlertDto>>

    @POST("sos/distress")
    suspend fun sendDistressSignal(
        @Body payload: SosPayloadDto
    ): Response<SosResponseDto>

    @POST("sos/{sosId}/cancel")
    suspend fun cancelDistressSignal(
        @Path("sosId") sosId: String
    ): Response<Unit>
}
