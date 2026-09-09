package com.pukaar.android.data.crypto

import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.PrivateKey
import java.security.PublicKey
import java.security.Signature
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import javax.inject.Inject
import javax.inject.Singleton
import org.bouncycastle.util.encoders.Hex

@Singleton
class PukaarCryptoManager @Inject constructor() {

    private val localKeyPair: KeyPair by lazy {
        val generator = KeyPairGenerator.getInstance("EC", "BC")
        generator.initialize(256)
        generator.generateKeyPair()
    }

    val localPublicKeyHex: String
        get() = Hex.toHexString(localKeyPair.public.encoded)

    fun sign(payload: String): String {
        val signature = Signature.getInstance("SHA256withECDSA", "BC")
        signature.initSign(localKeyPair.private)
        signature.update(payload.toByteArray(Charsets.UTF_8))
        return Hex.toHexString(signature.sign())
    }

    fun verify(payload: String, signatureHex: String, publicKey: PublicKey): Boolean {
        return try {
            val signature = Signature.getInstance("SHA256withECDSA", "BC")
            signature.initVerify(publicKey)
            signature.update(payload.toByteArray(Charsets.UTF_8))
            signature.verify(Hex.decode(signatureHex))
        } catch (e: Exception) {
            false
        }
    }

    fun encrypt(plainText: String, secretKey: SecretKey): Pair<String, String> {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding", "BC")
        cipher.init(Cipher.ENCRYPT_MODE, secretKey)
        val iv = cipher.iv
        val encrypted = cipher.doFinal(plainText.toByteArray(Charsets.UTF_8))
        return Pair(Hex.toHexString(encrypted), Hex.toHexString(iv))
    }

    fun decrypt(cipherHex: String, ivHex: String, secretKey: SecretKey): String {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding", "BC")
        val spec = GCMParameterSpec(128, Hex.decode(ivHex))
        cipher.init(Cipher.DECRYPT_MODE, secretKey, spec)
        val decryptedBytes = cipher.doFinal(Hex.decode(cipherHex))
        return String(decryptedBytes, Charsets.UTF_8)
    }

    fun generateSymmetricMeshKey(): SecretKey {
        val keyGen = KeyGenerator.getInstance("AES", "BC")
        keyGen.init(256)
        return keyGen.generateKey()
    }
}
