package com.pukaar.android.data.demo

import com.pukaar.android.domain.model.Alert
import com.pukaar.android.domain.model.CycloneData
import com.pukaar.android.domain.model.CyclonePoint
import com.pukaar.android.domain.model.MeshPeer
import com.pukaar.android.domain.model.RiskLevel
import com.pukaar.android.domain.model.SosMessage
import com.pukaar.android.domain.model.SosStatus

object DemoDataGenerator {

    fun generateCyclone(): CycloneData {
        val now = System.currentTimeMillis()
        val trajectory = listOf(
            CyclonePoint(now - 7200000, 18.2, 86.4, 95.0, "Cat 2 (Deep Sea)"),
            CyclonePoint(now - 3600000, 18.7, 86.1, 110.0, "Cat 3 (Approaching)"),
            CyclonePoint(now, 19.3, 85.8, 125.0, "Cat 4 (Current)"),
            CyclonePoint(now + 14400000, 19.9, 85.5, 135.0, "Cat 4 (Peak)"),
            CyclonePoint(now + 28800000, 20.3, 85.2, 115.0, "Landfall Zone"),
            CyclonePoint(now + 43200000, 20.7, 84.9, 85.0, "Inland Dissipation")
        )

        val evacuationPath = listOf(
            Pair(19.8135, 85.8312),
            Pair(19.8285, 85.8212),
            Pair(19.8435, 85.8092),
            Pair(19.8585, 85.7962)
        )

        return CycloneData(
            cycloneId = "CYC_PUKAAR_01",
            name = "Super Cyclone Varuna",
            centerLat = 19.3,
            centerLon = 85.8,
            currentWindSpeedKts = 125.0,
            centralPressureHpa = 932.0,
            r34Km = 240.0,
            r50Km = 140.0,
            r64Km = 75.0,
            landfallEtaTimestamp = now + 28800000,
            landfallProbability = 0.94,
            category = "Category 4 Very Severe Cyclonic Storm",
            riskLevel = RiskLevel.EXTREME,
            trajectory = trajectory,
            safetyEvacuationPath = evacuationPath,
            lastUpdated = now
        )
    }

    fun generateAlerts(): List<Alert> {
        val now = System.currentTimeMillis()
        return listOf(
            Alert(
                id = "alt_pukaar_01",
                title = "Extreme Threat: Storm Surge Inundation",
                description = "4.5m storm surges expected along Puri-Paradip coastline within 6 hours.",
                riskLevel = RiskLevel.EXTREME,
                category = "STORM_SURGE",
                zone = "Puri Coastal Belt",
                timestamp = now - 1800000,
                expiresAt = now + 86400000,
                actionAdvice = "Immediately evacuate low-lying sectors to Reinforced Shelter Alpha.",
                isMeshRelayed = true
            ),
            Alert(
                id = "alt_pukaar_02",
                title = "High Risk: Wind Gust Barrier Breach",
                description = "Severe gusts over 135 kts will compromise temporary roofing & power transmission lines.",
                riskLevel = RiskLevel.HIGH,
                category = "WIND_GUST",
                zone = "District Core",
                timestamp = now - 3600000,
                expiresAt = now + 43200000,
                actionAdvice = "Secure window shutters. Do not venture outdoors under any circumstances.",
                isMeshRelayed = true
            ),
            Alert(
                id = "alt_pukaar_03",
                title = "Moderate Caution: Power Grid Standby",
                description = "Proactive grid de-energization in effect to avoid electrical fire hazards.",
                riskLevel = RiskLevel.MODERATE,
                category = "POWER_GRID",
                zone = "All Sectors",
                timestamp = now - 7200000,
                expiresAt = now + 172800000,
                actionAdvice = "Switch devices to battery saver mode. Rely on Bluetooth mesh relay for SOS.",
                isMeshRelayed = false
            )
        )
    }

    fun generatePeers(): List<MeshPeer> {
        val now = System.currentTimeMillis()
        return listOf(
            MeshPeer("node_ndrf_01", "NDRF Rescue Post Alpha", -52, 1, true, now),
            MeshPeer("node_shelter_east", "Cyclone Shelter 9", -68, 2, true, now - 12000),
            MeshPeer("node_ham_radio", "Citizen Ham Radio #4", -81, 3, true, now - 45000),
            MeshPeer("node_community_hub", "Community Health Center", -74, 2, true, now - 22000)
        )
    }

    fun generateInitialSosInbox(): List<SosMessage> {
        val now = System.currentTimeMillis()
        return listOf(
            SosMessage(
                id = "SOS_MSG_001",
                senderId = "node_relay_bravo",
                senderName = "Puri Sector 4 Group",
                latitude = 19.824,
                longitude = 85.845,
                emergencyType = "TRAPPED",
                victimCount = 4,
                notes = "Water entering ground floor. Need boat evacuation.",
                timestamp = now - 900000,
                hopCount = 2,
                status = SosStatus.RELAYED_BY_PEERS
            ),
            SosMessage(
                id = "SOS_MSG_002",
                senderId = "node_citizen_99",
                senderName = "Village Elder Relatives",
                latitude = 19.805,
                longitude = 85.815,
                emergencyType = "MEDICAL",
                victimCount = 1,
                notes = "Elderly patient requires insulin & dry shelter.",
                timestamp = now - 2400000,
                hopCount = 1,
                status = SosStatus.RECEIVED_BY_RESCUE
            )
        )
    }
}
