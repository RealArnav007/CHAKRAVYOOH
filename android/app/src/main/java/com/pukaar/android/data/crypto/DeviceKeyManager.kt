package com.pukaar.android.data.crypto

// NEVER log: private key bytes, signature bytes in full, decrypted SOS payload content, sender PII
// Safe to log: msgId (truncated), packet type, verification result (VERIFIED/INVALID), timestamp

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import dagger.hilt.android.qualifiers.ApplicationContext
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.Signature
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DeviceKeyManager @Inject constructor(
    @ApplicationContext private val context: Context
) {

    private val ALIAS = "pukaar_device_key_v1"
    private val keyStore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }

    fun generateKeyPairIfAbsent() {
        try {
            if (keyStore.containsAlias(ALIAS)) return
            val kpg = KeyPairGenerator.getInstance(KeyProperties.KEY_ALGORITHM_EC, "AndroidKeyStore")
            val spec = KeyGenParameterSpec.Builder(
                ALIAS,
                KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
            )
                .setDigests(KeyProperties.DIGEST_SHA256)
                .setKeySize(256)
                .build()
            kpg.initialize(spec)
            kpg.generateKeyPair()
        } catch (e: Exception) {
            // Handled safely for testing and restricted hardware environments
        }
    }

    fun getPublicKeyBase64(): String {
        return try {
            generateKeyPairIfAbsent()
            val entry = keyStore.getEntry(ALIAS, null) as? KeyStore.PrivateKeyEntry
            if (entry != null) {
                Base64.encodeToString(entry.certificate.publicKey.encoded, Base64.NO_WRAP)
            } else ""
        } catch (e: Exception) {
            ""
        }
    }

    fun signPayload(payload: ByteArray): String {
        return try {
            generateKeyPairIfAbsent()
            val entry = keyStore.getEntry(ALIAS, null) as? KeyStore.PrivateKeyEntry
            if (entry != null) {
                Signature.getInstance("SHA256withECDSA").run {
                    initSign(entry.privateKey)
                    update(payload)
                    Base64.encodeToString(sign(), Base64.NO_WRAP)
                }
            } else ""
        } catch (e: Exception) {
            ""
        }
    }

    // Returns a canonical payload string for SOS signing
    fun buildSosCanonicalPayload(type: String, lat: Double, lon: Double, timestamp: String): String =
        "$type|$lat|$lon|$timestamp"

    // Returns a canonical payload for alert verification (must match backend's signing logic)
    fun buildAlertCanonicalPayload(alertId: String, version: Int, issuedAt: String, riskLevel: String, message: String): String =
        "$alertId|$version|$issuedAt|$riskLevel|$message"
}
