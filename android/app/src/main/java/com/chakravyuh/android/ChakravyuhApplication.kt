package com.chakravyuh.android

import android.app.Application
import dagger.hilt.android.HiltAndroidApp
import java.security.Security
import org.bouncycastle.jce.provider.BouncyCastleProvider

/**
 * Main Application class for Chakravyuh disaster intelligence & mesh resilience platform.
 * Initializes Hilt dependency injection container and BouncyCastle security provider.
 */
@HiltAndroidApp
class ChakravyuhApplication : Application() {

    override fun onCreate() {
        super.onCreate()
        setupSecurityProvider()
    }

    private fun setupSecurityProvider() {
        // Register BouncyCastle Provider for offline mesh cryptographic signing & encryption
        Security.removeProvider(BouncyCastleProvider.PROVIDER_NAME)
        Security.addProvider(BouncyCastleProvider())
    }
}
