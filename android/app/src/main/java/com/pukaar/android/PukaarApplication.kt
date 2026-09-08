package com.pukaar.android

import android.app.Application
import dagger.hilt.android.HiltAndroidApp
import java.security.Security
import org.bouncycastle.jce.provider.BouncyCastleProvider

@HiltAndroidApp
class PukaarApplication : Application() {

    override fun onCreate() {
        super.onCreate()
        setupBouncyCastle()
    }

    private fun setupBouncyCastle() {
        Security.removeProvider(BouncyCastleProvider.PROVIDER_NAME)
        Security.addProvider(BouncyCastleProvider())
    }
}
