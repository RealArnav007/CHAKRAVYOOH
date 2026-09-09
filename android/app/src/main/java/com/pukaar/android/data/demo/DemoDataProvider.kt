package com.pukaar.android.data.demo

import com.pukaar.android.domain.model.CycloneAlert
import com.pukaar.android.domain.model.CycloneIntelligence
import com.pukaar.android.domain.model.CycloneStage
import com.pukaar.android.domain.model.DeliveryStatus
import com.pukaar.android.domain.model.EmergencyType
import com.pukaar.android.domain.model.GatewayStatus
import com.pukaar.android.domain.model.IncomingSos
import com.pukaar.android.domain.model.IntensityLevel
import com.pukaar.android.domain.model.LatLng
import com.pukaar.android.domain.model.MeshStatus
import com.pukaar.android.domain.model.MeshTransport
import com.pukaar.android.domain.model.PathPoint
import com.pukaar.android.domain.model.RelayStatus
import com.pukaar.android.domain.model.RiskLevel
import com.pukaar.android.domain.model.RiskZone
import com.pukaar.android.domain.model.VerificationStatus
import java.time.Instant

object DemoDataProvider {

    fun getCycloneIntelligence(): CycloneIntelligence = CycloneIntelligence(
        cycloneId = "CY-2026-001",
        timestamp = Instant.now().toString(),
        detected = true,
        detectionConfidence = 0.94,
        classificationStage = CycloneStage.MATURE_TROPICAL_CYCLONE,
        classificationConfidence = 0.92,
        intensityLevel = IntensityLevel.HIGH,
        intensityConfidence = 0.89,
        currentPosition = LatLng(13.0, 74.5),   // Arabian Sea
        heading = "NORTH_WEST",
        forecastHours = 24,
        predictionConfidence = 0.88,
        predictedPath = listOf(
            PathPoint(6,  14.2, 73.1),
            PathPoint(12, 15.8, 71.9),
            PathPoint(24, 18.3, 70.2)
        ),
        uncertaintyRadiusKm = 75.0,
        generatedAt = Instant.now().toString(),
        validUntil = Instant.now().plusSeconds(7200).toString()
    )

    fun getRiskZones(): List<RiskZone> = listOf(
        RiskZone(
            zoneId = "Z1",
            zoneName = "Konkan Coast",
            riskLevel = RiskLevel.EXTREME,
            polygon = listOf(
                LatLng(15.0, 73.5),
                LatLng(17.5, 73.0),
                LatLng(17.8, 73.8),
                LatLng(15.2, 74.2)
            )
        ),
        RiskZone(
            zoneId = "Z2",
            zoneName = "Western Ghats",
            riskLevel = RiskLevel.HIGH,
            polygon = listOf(
                LatLng(14.5, 74.2),
                LatLng(17.5, 73.8),
                LatLng(17.7, 74.5),
                LatLng(14.7, 75.0)
            )
        ),
        RiskZone(
            zoneId = "Z3",
            zoneName = "Deccan Plateau",
            riskLevel = RiskLevel.MODERATE,
            polygon = listOf(
                LatLng(14.0, 75.0),
                LatLng(17.5, 74.5),
                LatLng(17.5, 76.5),
                LatLng(14.0, 76.8)
            )
        ),
        RiskZone(
            zoneId = "Z4",
            zoneName = "Eastern India",
            riskLevel = RiskLevel.LOW,
            polygon = listOf(
                LatLng(13.0, 77.0),
                LatLng(18.0, 77.0),
                LatLng(18.0, 82.0),
                LatLng(13.0, 82.0)
            )
        )
    )

    fun getAlert(): CycloneAlert = CycloneAlert(
        alertId = "ALT-001",
        version = 1,
        issuedAt = Instant.now().toString(),
        updatedAt = Instant.now().toString(),
        validUntil = Instant.now().plusSeconds(7200).toString(),
        supersedes = null,
        riskLevel = RiskLevel.EXTREME,
        message = "Severe cyclonic storm VAYU-2026 approaching Konkan coast. Mandatory evacuation for Zone A. Move inland immediately.",
        affectedZones = listOf("Konkan Coast", "Western Ghats"),
        signature = "DEMO_SIGNATURE_BASE64",
        verificationStatus = VerificationStatus.VERIFIED
    )

    fun getAlerts(): List<CycloneAlert> = listOf(getAlert())

    fun getMeshStatus(): MeshStatus = MeshStatus(
        internetOnline = false,
        meshActive = true,
        nearbyRelayCount = 3,
        gatewayStatus = GatewayStatus.SEARCHING,
        deliveryStatus = DeliveryStatus.PENDING,
        transport = MeshTransport.WIFI_AWARE
    )

    fun getIncomingSos(): IncomingSos = IncomingSos(
        msgId = "SOS-DEMO-001",
        senderHash = "a3f9b2c1",
        emergencyType = EmergencyType.FLOOD,
        latitude = 15.5,
        longitude = 73.8,
        message = "Flooding on ground floor. Cannot evacuate.",
        receivedAt = System.currentTimeMillis(),
        hopCount = 2,
        transport = MeshTransport.BLUETOOTH,
        relayStatus = RelayStatus.PENDING,
        verificationStatus = VerificationStatus.VERIFIED
    )

    fun getIncomingSosList(): List<IncomingSos> = listOf(getIncomingSos())
}
