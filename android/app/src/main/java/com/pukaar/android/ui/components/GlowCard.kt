package com.pukaar.android.ui.components

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.pukaar.android.ui.theme.PukaarColors

@Composable
fun GlowCard(
    modifier: Modifier = Modifier,
    glowColor: Color = PukaarColors.AccentCyan,
    pulse: Boolean = false,
    cornerRadius: Dp = 12.dp,
    content: @Composable BoxScope.() -> Unit
) {
    val infiniteTransition = rememberInfiniteTransition(label = "glow_pulse")
    val alphaAnim by if (pulse) {
        infiniteTransition.animateFloat(
            initialValue = 0.4f,
            targetValue = 1.0f,
            animationSpec = infiniteRepeatable(
                animation = tween(durationMillis = 700, easing = FastOutSlowInEasing),
                repeatMode = RepeatMode.Reverse
            ),
            label = "border_alpha"
        )
    } else {
        rememberInfiniteTransition(label = "static_alpha").animateFloat(
            initialValue = 0.4f,
            targetValue = 0.4f,
            animationSpec = infiniteRepeatable(tween(1000)),
            label = "static"
        )
    }

    Box(
        modifier = modifier
            .drawBehind {
                // 2dp blur-like effect: 3 concentric outer rectangles
                val strokeWidth = 2.dp.toPx()
                val radii = cornerRadius.toPx()

                // Outer-most subtle halo
                drawRoundRect(
                    color = glowColor.copy(alpha = 0.03f),
                    topLeft = Offset(-4f, -4f),
                    size = Size(size.width + 8f, size.height + 8f),
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(radii + 4f, radii + 4f),
                    style = Stroke(width = strokeWidth * 2)
                )

                // Middle halo
                drawRoundRect(
                    color = glowColor.copy(alpha = 0.08f),
                    topLeft = Offset(-2f, -2f),
                    size = Size(size.width + 4f, size.height + 4f),
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(radii + 2f, radii + 2f),
                    style = Stroke(width = strokeWidth)
                )

                // Inner glow halo
                drawRoundRect(
                    color = glowColor.copy(alpha = 0.15f),
                    topLeft = Offset(-1f, -1f),
                    size = Size(size.width + 2f, size.height + 2f),
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(radii + 1f, radii + 1f),
                    style = Stroke(width = 1f)
                )
            }
            .clip(RoundedCornerShape(cornerRadius))
            .background(PukaarColors.BgSurface)
            .drawWithContent {
                drawContent()
                // Top border 1dp with animated/static alpha
                val currentAlpha = if (pulse) alphaAnim else 0.4f
                drawLine(
                    color = glowColor.copy(alpha = currentAlpha),
                    start = Offset(0f, 0f),
                    end = Offset(size.width, 0f),
                    strokeWidth = 1.dp.toPx()
                )
            }
            .padding(16.dp),
        content = content
    )
}
