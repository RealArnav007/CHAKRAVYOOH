package com.pukaar.android.demo

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.pukaar.android.data.demo.DemoDataProvider
import com.pukaar.android.data.demo.DemoModeRepository
import com.pukaar.android.data.local.UserPreferences
import com.pukaar.android.domain.model.CycloneAlert
import com.pukaar.android.domain.model.CycloneIntelligence
import com.pukaar.android.domain.model.CycloneStage
import com.pukaar.android.domain.model.IncomingSos
import com.pukaar.android.domain.model.IntensityLevel
import com.pukaar.android.domain.model.LatLng
import com.pukaar.android.domain.model.MeshPacket
import com.pukaar.android.domain.model.MeshStatus
import com.pukaar.android.domain.model.PacketLogEntry
import com.pukaar.android.domain.model.RelayStatus
import com.pukaar.android.domain.model.RiskZone
import com.pukaar.android.domain.model.SosRequest
import com.pukaar.android.domain.repository.AlertRepository
import com.pukaar.android.domain.repository.CycloneEvent
import com.pukaar.android.domain.repository.CycloneRepository
import com.pukaar.android.domain.repository.MeshRepository
import com.pukaar.android.domain.repository.RiskZoneRepository
import com.pukaar.android.domain.repository.SosRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.emptyFlow
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class DemoModeTest {

    private lateinit var userPreferences: UserPreferences
    private lateinit var demoModeRepository: DemoModeRepository

    private val realCyclone = CycloneIntelligence(
        cycloneId = "CY-REAL-999",
        timestamp = "2026-09-09T00:00:00Z",
        detected = false,
        detectionConfidence = 0.1,
        classificationStage = CycloneStage.DEVELOPING_DISTURBANCE,
        classificationConfidence = 0.2,
        intensityLevel = IntensityLevel.LOW,
        intensityConfidence = 0.3,
        currentPosition = LatLng(10.0, 80.0),
        heading = "NORTH",
        forecastHours = 12,
        predictionConfidence = 0.5,
        predictedPath = emptyList(),
        uncertaintyRadiusKm = 50.0,
        generatedAt = "2026-09-09T00:00:00Z",
        validUntil = "2026-09-09T02:00:00Z"
    )

    private val fakeRealCycloneRepo = object : CycloneRepository {
        override suspend fun getActiveCyclones(): Result<List<CycloneIntelligence>> =
            Result.success(listOf(realCyclone))

        override suspend fun getCycloneById(id: String): Result<CycloneIntelligence> =
            Result.success(realCyclone)

        override fun observeCycloneEvents(): Flow<CycloneEvent> = emptyFlow()
    }

    private val fakeRealAlertRepo = object : AlertRepository {
        override suspend fun getAlerts(): Result<List<CycloneAlert>> = Result.success(emptyList())
        override fun observeAlertEvents(): Flow<CycloneAlert> = emptyFlow()
    }

    private val fakeRealRiskZoneRepo = object : RiskZoneRepository {
        override suspend fun getRiskZones(): Result<List<RiskZone>> = Result.success(emptyList())
    }

    private val fakeRealMeshRepo = object : MeshRepository {
        override fun observeMeshStatus(): Flow<MeshStatus> = emptyFlow()
        override suspend fun relayPacket(packet: MeshPacket): Result<Unit> = Result.success(Unit)
        override fun observePacketLog(): Flow<List<PacketLogEntry>> = emptyFlow()
    }

    private val fakeRealSosRepo = object : SosRepository {
        override suspend fun sendSos(request: SosRequest): Result<String> = Result.success("REAL-SOS-ID")
        override fun observeIncomingSos(): Flow<List<IncomingSos>> = emptyFlow()
        override suspend fun getInboxSnapshot(): List<IncomingSos> = emptyList()
        override suspend fun updateRelayStatus(msgId: String, status: RelayStatus) {}
    }

    @Before
    fun setUp() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        userPreferences = UserPreferences(context)
        demoModeRepository = DemoModeRepository(
            realCycloneRepo = fakeRealCycloneRepo,
            realAlertRepo = fakeRealAlertRepo,
            realRiskZoneRepo = fakeRealRiskZoneRepo,
            realMeshRepo = fakeRealMeshRepo,
            realSosRepo = fakeRealSosRepo,
            userPreferences = userPreferences
        )
    }

    @Test
    fun testDemoModeDelegationToggle() = runBlocking {
        // 1. Enable Demo Mode
        userPreferences.setDemoMode(true)

        // 2. Call DemoModeRepository.getActiveCyclones() -> assert returns DemoDataProvider cyclone
        val demoCyclones = demoModeRepository.getActiveCyclones().getOrThrow()
        assertEquals(1, demoCyclones.size)
        assertEquals("CY-2026-001", demoCyclones.first().cycloneId)
        assertEquals(DemoDataProvider.getCycloneIntelligence().cycloneId, demoCyclones.first().cycloneId)

        // Also verify Demo alerts, risk zones, and incoming SOS
        val demoAlerts = demoModeRepository.getAlerts().getOrThrow()
        assertEquals("ALT-001", demoAlerts.first().alertId)

        val demoRiskZones = demoModeRepository.getRiskZones().getOrThrow()
        assertEquals(4, demoRiskZones.size)

        val demoSos = demoModeRepository.getInboxSnapshot()
        assertEquals("SOS-DEMO-001", demoSos.first().msgId)

        // 3. Disable Demo Mode -> assert delegates to real impl
        userPreferences.setDemoMode(false)

        val realCyclones = demoModeRepository.getActiveCyclones().getOrThrow()
        assertEquals(1, realCyclones.size)
        assertEquals("CY-REAL-999", realCyclones.first().cycloneId)

        val realAlerts = demoModeRepository.getAlerts().getOrThrow()
        assertEquals(0, realAlerts.size)
    }
}
