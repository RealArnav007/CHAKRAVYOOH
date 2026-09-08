package com.chakravyuh.android.data.mesh

import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.PrivateKey
import java.security.PublicKey
import java.security.Signature
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec
import javax.inject.Inject
import javax.inject.Singleton
import org.bouncycastle.util.encoders.Hex

/**
 * Cryptographic utility utilizing BouncyCastle for offline mesh packet authentication,
 * digital signatures (ECDSA), and symmetric encryption (AES-256-GCM).
 */
@Singleton
class MeshCryptoHelper @Inject constructor() {

    private val localKeyPair: KeyPair by lazy {
        val keyGen = KeyPairGenerator.getInstance("EC", "BC")
        keyGen.initialize(256)
        keyGen.generateKeyPair()
    }

    val publicKeyHex: String
        get() = Hex.toHexString(localKeyPair.public.encoded)

    fun signData(data: ByteArray, privateKey: PrivateKey = localKeyPair.private): String {
        val signature = Signature.getInstance("SHA256withECDSA", "BC")
        signature.initSign(privateKey)
        signature.update(data)
        return Hex.toHexString(signature.sign())
    }

    fun verifySignature(data: ByteArray, signatureHex: String, publicKey: PublicKey): Boolean {
        return try {
            val signature = Signature.getInstance("SHA256withECDSA", "BC")
            signature.initVerify(publicKey)
            signature.update(data)
            signature.verify(Hex.decode(signatureHex))
        } catch (e: Exception) {
            false
        }
    }

    fun encryptPayload(plainText: String, secretKey: SecretKey): Pair<String, String> {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding", "BC")
        cipher.init(Cipher.ENCRYPT_MODE, secretKey)
        val iv = cipher.iv
        val cipherText = cipher.doFinal(plainText.toByteArray(Charsets.UTF_8))
        return Pair(Hex.toHexString(cipherText), Hex.toHexString(iv))
    }

    fun decryptPayload(cipherHex: String, ivHex: String, secretKey: SecretKey): String {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding", "BC")
        val spec = GCMParameterSpec(128, Hex.decode(ivHex))
        cipher.init(Cipher.DECRYPT_MODE, secretKey, spec)
        val plainBytes = cipher.doFinal(Hex.decode(cipherHex))
        return String(plainBytes, Charsets.UTF_8)
    }

    fun generateSharedMeshKey(): SecretKey {
        val keyGen = KeyGenerator.getInstance("AES", "BC")
        keyGen.init(256)
        return keyGen.generateKey()
    }
}
