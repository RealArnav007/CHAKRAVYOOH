package com.pukaar.android.ui.navigation

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Badge
import androidx.compose.material3.BadgedBox
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.currentBackStackEntryAsState
import com.pukaar.android.ui.theme.PukaarColors

@Composable
fun BottomNavBar(
    navController: NavController,
    unreadAlertsCount: Int = 3,
    modifier: Modifier = Modifier
) {
    val items = Screen.bottomNavScreens
    val navBackStackEntry = navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry.value?.destination?.route

    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(PukaarColors.BgVoid)
            .drawBehind {
                // Top subtle border line
                drawLine(
                    color = PukaarColors.BgElevated,
                    start = Offset(0f, 0f),
                    end = Offset(size.width, 0f),
                    strokeWidth = 1.dp.toPx()
                )
            }
            .padding(horizontal = 8.dp, vertical = 6.dp),
        horizontalArrangement = Arrangement.SpaceAround,
        verticalAlignment = Alignment.CenterVertically
    ) {
        items.forEach { screen ->
            val isSelected = currentRoute == screen.route
            val isSos = screen == Screen.Sos
            val activeColor = if (isSos) PukaarColors.AccentRed else PukaarColors.AccentCyan
            val inactiveColor = if (isSos) PukaarColors.AccentRed.copy(alpha = 0.7f) else PukaarColors.TextSecondary

            val itemColor = if (isSelected) activeColor else inactiveColor
            val interactionSource = remember { MutableInteractionSource() }

            Column(
                modifier = Modifier
                    .clickable(
                        interactionSource = interactionSource,
                        indication = null
                    ) {
                        if (currentRoute != screen.route) {
                            navController.navigate(screen.route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        }
                    }
                    .padding(vertical = 4.dp, horizontal = 10.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Underline indicator when selected (Cyan/Red top indicator bar)
                Box(
                    modifier = Modifier
                        .size(width = 24.dp, height = 2.dp)
                        .background(if (isSelected) activeColor else Color.Transparent)
                )

                Spacer(modifier = Modifier.height(4.dp))

                if (screen == Screen.Alerts && unreadAlertsCount > 0) {
                    BadgedBox(
                        badge = {
                            Badge(
                                containerColor = PukaarColors.AccentRed,
                                contentColor = Color.White
                            ) {
                                Text(
                                    text = "$unreadAlertsCount",
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }
                    ) {
                        Icon(
                            imageVector = screen.icon!!,
                            contentDescription = screen.title,
                            tint = itemColor,
                            modifier = Modifier.size(24.dp)
                        )
                    }
                } else {
                    Icon(
                        imageVector = screen.icon!!,
                        contentDescription = screen.title,
                        tint = itemColor,
                        modifier = Modifier.size(if (isSos) 28.dp else 24.dp)
                    )
                }

                Spacer(modifier = Modifier.height(2.dp))

                Text(
                    text = screen.title.uppercase(),
                    style = MaterialTheme.typography.labelSmall.copy(
                        fontSize = if (isSos) 11.sp else 10.sp,
                        fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal
                    ),
                    color = itemColor
                )
            }
        }
    }
}
