package com.pukaar.android.ui.screens.sos

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.TabRowDefaults.tabIndicatorOffset
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.pukaar.android.ui.screens.sos.inbox.SosInboxScreen
import com.pukaar.android.ui.screens.sos.inbox.SosInboxViewModel
import com.pukaar.android.ui.screens.sos.send.SosSendScreen
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily
import kotlinx.coroutines.launch

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun SosScreen(
    onNavigateToSettings: () -> Unit = {},
    inboxViewModel: SosInboxViewModel = hiltViewModel()
) {
    val inboxState by inboxViewModel.state.collectAsState()
    val pagerState = rememberPagerState(pageCount = { 2 })
    val coroutineScope = rememberCoroutineScope()

    val tabs = listOf(
        "SEND",
        if (inboxState.incoming.isNotEmpty()) "INBOX (${inboxState.incoming.size})" else "INBOX"
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(PukaarColors.BgVoid)
    ) {
        // TabRow with Custom 2dp AccentRed Indicator
        TabRow(
            selectedTabIndex = pagerState.currentPage,
            containerColor = PukaarColors.BgSurface,
            contentColor = PukaarColors.AccentRed,
            indicator = { tabPositions ->
                if (pagerState.currentPage < tabPositions.size) {
                    Box(
                        modifier = Modifier
                            .tabIndicatorOffset(tabPositions[pagerState.currentPage])
                            .fillMaxWidth()
                            .height(2.dp)
                            .background(PukaarColors.AccentRed)
                    )
                }
            },
            divider = {}
        ) {
            tabs.forEachIndexed { index, title ->
                val selected = pagerState.currentPage == index
                Tab(
                    selected = selected,
                    onClick = {
                        coroutineScope.launch {
                            pagerState.animateScrollToPage(index)
                        }
                    },
                    text = {
                        Text(
                            text = title,
                            fontFamily = RajdhaniFontFamily,
                            fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium,
                            fontSize = 14.sp,
                            color = if (selected) PukaarColors.AccentRed else PukaarColors.TextSecondary
                        )
                    }
                )
            }
        }

        // Horizontal Pager for Tab Switching
        HorizontalPager(
            state = pagerState,
            modifier = Modifier.fillMaxSize()
        ) { page ->
            when (page) {
                0 -> SosSendScreen()
                1 -> SosInboxScreen(viewModel = inboxViewModel)
            }
        }
    }
}
