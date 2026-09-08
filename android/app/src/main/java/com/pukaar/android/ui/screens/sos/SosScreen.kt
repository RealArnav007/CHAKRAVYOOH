package com.pukaar.android.ui.screens.sos

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pukaar.android.ui.components.StatusDot
import com.pukaar.android.ui.screens.sos.inbox.SosInboxScreen
import com.pukaar.android.ui.screens.sos.send.SosSendScreen
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily

enum class SosTab {
    SEND, INBOX
}

@Composable
fun SosScreen(
    onNavigateToSettings: () -> Unit
) {
    var selectedTab by remember { mutableStateOf(SosTab.SEND) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(PukaarColors.BgVoid)
    ) {
        // Top Header
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                StatusDot(color = PukaarColors.AccentRed)
                Text(
                    text = "PUKAAR SOS",
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 22.sp,
                    letterSpacing = 1.5.sp,
                    color = PukaarColors.AccentRed
                )
            }

            IconButton(onClick = onNavigateToSettings) {
                Icon(
                    imageVector = Icons.Default.Settings,
                    contentDescription = "Settings",
                    tint = PukaarColors.TextSecondary
                )
            }
        }

        // Sub-Tab Switcher (Send / Inbox)
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 4.dp)
                .clip(RoundedCornerShape(8.dp))
                .background(PukaarColors.BgSurface)
        ) {
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(8.dp))
                    .background(if (selectedTab == SosTab.SEND) PukaarColors.AccentRed else PukaarColors.BgSurface)
                    .clickable { selectedTab = SosTab.SEND }
                    .padding(vertical = 10.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "SEND DISTRESS",
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    color = if (selectedTab == SosTab.SEND) PukaarColors.BgVoid else PukaarColors.TextSecondary
                )
            }

            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(8.dp))
                    .background(if (selectedTab == SosTab.INBOX) PukaarColors.AccentCyan else PukaarColors.BgSurface)
                    .clickable { selectedTab = SosTab.INBOX }
                    .padding(vertical = 10.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "MESH INBOX",
                    fontFamily = RajdhaniFontFamily,
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    color = if (selectedTab == SosTab.INBOX) PukaarColors.BgVoid else PukaarColors.TextSecondary
                )
            }
        }

        // Content
        when (selectedTab) {
            SosTab.SEND -> SosSendScreen()
            SosTab.INBOX -> SosInboxScreen()
        }
    }
}
