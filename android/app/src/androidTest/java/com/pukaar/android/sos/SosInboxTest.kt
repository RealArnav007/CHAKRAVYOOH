package com.pukaar.android.sos

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.pukaar.android.data.local.PukaarDatabase
import com.pukaar.android.data.local.dao.IncomingSosDao
import com.pukaar.android.data.local.entity.IncomingSosEntity
import com.pukaar.android.domain.model.EmergencyType
import com.pukaar.android.domain.model.MeshTransport
import com.pukaar.android.domain.model.RelayStatus
import com.pukaar.android.domain.model.VerificationStatus
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class SosInboxTest {

    private lateinit var database: PukaarDatabase
    private lateinit var incomingSosDao: IncomingSosDao

    @Before
    fun setUp() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        database = Room.inMemoryDatabaseBuilder(context, PukaarDatabase::class.java)
            .allowMainThreadQueries()
            .build()
        incomingSosDao = database.incomingSosDao()
    }

    @After
    fun tearDown() {
        database.close()
    }

    @Test
    fun testSosInboxInsertionAndRelayStatusUpdate() = runBlocking {
        // 1. Insert 3 IncomingSosEntity into Room
        val e1 = IncomingSosEntity(
            msgId = "SOS-001",
            senderHash = "hash-1",
            emergencyType = EmergencyType.MEDICAL.name,
            latitude = 15.5,
            longitude = 73.8,
            message = "Need oxygen support immediately.",
            receivedAt = System.currentTimeMillis() - 3000,
            hopCount = 1,
            transport = MeshTransport.BLUETOOTH.name,
            relayStatus = RelayStatus.PENDING.name,
            verificationStatus = VerificationStatus.VERIFIED.name
        )
        val e2 = IncomingSosEntity(
            msgId = "SOS-002",
            senderHash = "hash-2",
            emergencyType = EmergencyType.FLOOD.name,
            latitude = 15.6,
            longitude = 73.9,
            message = "Roof rescue required.",
            receivedAt = System.currentTimeMillis() - 2000,
            hopCount = 2,
            transport = MeshTransport.WIFI_AWARE.name,
            relayStatus = RelayStatus.PENDING.name,
            verificationStatus = VerificationStatus.VERIFIED.name
        )
        val e3 = IncomingSosEntity(
            msgId = "SOS-003",
            senderHash = "hash-3",
            emergencyType = EmergencyType.TRAPPED.name,
            latitude = 15.7,
            longitude = 74.0,
            message = "Basement collapsed.",
            receivedAt = System.currentTimeMillis() - 1000,
            hopCount = 3,
            transport = MeshTransport.BLUETOOTH.name,
            relayStatus = RelayStatus.PENDING.name,
            verificationStatus = VerificationStatus.VERIFIED.name
        )

        incomingSosDao.insertOrReplace(e1)
        incomingSosDao.insertOrReplace(e2)
        incomingSosDao.insertOrReplace(e3)

        // 2. Collect IncomingSosDao.getAllAsFlow() -> assert list size = 3
        val initialList = incomingSosDao.getAllAsFlow().first()
        assertEquals(3, initialList.size)

        // 3. Call updateRelayStatus(msgId, RELAYED) -> collect again -> assert status updated
        incomingSosDao.updateRelayStatus("SOS-001", RelayStatus.RELAYED.name)

        val updatedList = incomingSosDao.getAllAsFlow().first()
        val updatedE1 = updatedList.firstOrNull { it.msgId == "SOS-001" }

        assertEquals(RelayStatus.RELAYED.name, updatedE1?.relayStatus)
    }
}
