package com.pukaar.android.crypto

import android.util.Base64
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.pukaar.android.data.crypto.AlertVerificationService
import com.pukaar.android.domain.model.CycloneAlert
import com.pukaar.android.domain.model.RiskLevel
import com.pukaar.android.domain.model.VerificationStatus
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.security.KeyPairGenerator
import java.security.Signature
import java.security.spec.ECGenParameterSpec

@RunWith(AndroidJUnit4::class)
class AlertVerificationTest {

    private lateinit var service: AlertVerificationService

    @Before
    fun setUp() {
        service = AlertVerificationService()
    }

    @Test
    fun testAlertSignatureVerification() {
        // 1. Generate EC keypair in test
        val kpg = KeyPairGenerator.getInstance("EC")
        kpg.initialize(ECGenParameterSpec("secp256r1"))
        val keyPair = kpg.generateKeyPair()

        val publicKeyB64 = Base64.encodeToString(keyPair.public.encoded, Base64.NO_WRAP)

        val rawAlert = CycloneAlert(
            alertId = "ALT-TEST-001",
            version = 1,
            issuedAt = "2026-09-09T06:00:00Z",
            updatedAt = "2026-09-09T06:00:00Z",
            validUntil = "2026-09-09T08:00:00Z",
            supersedes = null,
            riskLevel = RiskLevel.EXTREME,
            message = "Mandatory evacuation for Zone 1.",
            affectedZones = listOf("Zone 1"),
            signature = "",
            verificationStatus = VerificationStatus.PENDING
        )

        val canonical = service.buildCanonicalAlertPayload(rawAlert)

        // 2. Sign canonical alert payload with test private key
        val signer = Signature.getInstance("SHA256withECDSA")
        signer.initSign(keyPair.private)
        signer.update(canonical.toByteArray(Charsets.UTF_8))
        val sigBytes = signer.sign()
        val signatureB64 = Base64.encodeToString(sigBytes, Base64.NO_WRAP)

        val signedAlert = rawAlert.copy(signature = signatureB64)

        // 3. Pass signed alert to AlertVerificationService -> Assert VERIFIED
        val result = service.verifyAlert(signedAlert, customPublicKeyB64 = publicKeyB64)
        assertEquals(VerificationStatus.VERIFIED, result)

        // 4. Modify message -> Assert INVALID
        val tamperedAlert = signedAlert.copy(message = "Tampered evacuation message! Stay home.")
        val tamperedResult = service.verifyAlert(tamperedAlert, customPublicKeyB64 = publicKeyB64)
        assertEquals(VerificationStatus.INVALID, tamperedResult)
    }
}
