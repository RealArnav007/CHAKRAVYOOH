package com.pukaar.android.crypto

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.pukaar.android.data.crypto.ReplayProtectionManager
import com.pukaar.android.data.local.PukaarDatabase
import com.pukaar.android.domain.model.MeshPacket
import com.pukaar.android.domain.model.MeshPriority
import com.pukaar.android.domain.model.MessageType
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.time.Instant

@RunWith(AndroidJUnit4::class)
class ReplayProtectionTest {

    private lateinit var database: PukaarDatabase
    private lateinit var replayProtectionManager: ReplayProtectionManager

    @Before
    fun setUp() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        database = Room.inMemoryDatabaseBuilder(context, PukaarDatabase::class.java)
            .allowMainThreadQueries()
            .build()
        replayProtectionManager = ReplayProtectionManager(database.seenPacketDao())
    }

    @After
    fun tearDown() {
        database.close()
    }

    @Test
    fun testReplayProtectionAndTtl() = runBlocking {
        val now = Instant.now()

        val p1 = MeshPacket(
            msgId = "PKT-001",
            messageType = MessageType.SOS,
            createdAt = now.toString(),
            ttl = 5,
            hops = 0,
            priority = MeshPriority.P0,
            senderIdentity = "SENDER-A",
            signature = "SIG-A",
            encryptedPayload = "PAYLOAD-A"
        )

        // 1. First time processing P1 -> isDuplicate is false
        val isFirstTime = replayProtectionManager.isDuplicate(p1)
        assertFalse("First time packet should not be marked duplicate", isFirstTime)

        // 2. Second time processing P1 -> isDuplicate is true
        val isSecondTime = replayProtectionManager.isDuplicate(p1)
        assertTrue("Subsequent packet should be detected as duplicate", isSecondTime)

        // 3. Process packet P2 with createdAt = 10 minutes ago -> isDuplicate is true (clock skew)
        val p2 = MeshPacket(
            msgId = "PKT-002",
            messageType = MessageType.CYCLONE_WARNING,
            createdAt = now.minusSeconds(600).toString(),
            ttl = 5,
            hops = 0,
            priority = MeshPriority.P0,
            senderIdentity = "SENDER-B",
            signature = "SIG-B",
            encryptedPayload = "PAYLOAD-B"
        )
        val isClockSkewDuplicate = replayProtectionManager.isDuplicate(p2)
        assertTrue("Packet with large clock skew should be marked duplicate/invalid", isClockSkewDuplicate)

        // 4. Process packet P3 with ttl = 0 -> enforceTTL returns null
        val p3 = MeshPacket(
            msgId = "PKT-003",
            messageType = MessageType.RELAY,
            createdAt = now.toString(),
            ttl = 0,
            hops = 3,
            priority = MeshPriority.P1,
            senderIdentity = "SENDER-C",
            signature = "SIG-C",
            encryptedPayload = "PAYLOAD-C"
        )
        val p3Forwarded = replayProtectionManager.enforceTTL(p3)
        assertNull("Packet with ttl = 0 should not be forwarded (null)", p3Forwarded)

        // 5. Process packet P4 with ttl = 3 -> enforceTTL returns copy with ttl=2, hops incremented
        val p4 = MeshPacket(
            msgId = "PKT-004",
            messageType = MessageType.SOS,
            createdAt = now.toString(),
            ttl = 3,
            hops = 1,
            priority = MeshPriority.P0,
            senderIdentity = "SENDER-D",
            signature = "SIG-D",
            encryptedPayload = "PAYLOAD-D"
        )
        val p4Forwarded = replayProtectionManager.enforceTTL(p4)
        assertNotNull("Packet with ttl > 0 should be forwarded", p4Forwarded)
        assertEquals(2, p4Forwarded!!.ttl)
        assertEquals(2, p4Forwarded.hops)
    }
}
