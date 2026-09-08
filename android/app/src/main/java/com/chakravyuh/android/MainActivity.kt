package com.chakravyuh.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.chakravyuh.android.ui.ChakravyuhApp
import com.chakravyuh.android.ui.theme.ChakravyuhTheme
import dagger.hilt.android.AndroidEntryPoint

/**
 * Entry point activity hosting the Chakravyuh Compose UI root.
 */
@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        setContent {
            ChakravyuhTheme {
                ChakravyuhApp()
            }
        }
    }
}
