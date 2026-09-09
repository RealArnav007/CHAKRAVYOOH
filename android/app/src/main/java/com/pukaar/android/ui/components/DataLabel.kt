package com.pukaar.android.ui.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pukaar.android.ui.theme.PukaarColors
import com.pukaar.android.ui.theme.RajdhaniFontFamily

@Composable
fun DataLabel(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
    valueColor: Color = PukaarColors.TextPrimary,
    unit: String? = null
) {
    Column(modifier = modifier) {
        Text(
            text = label.uppercase(),
            style = MaterialTheme.typography.labelSmall.copy(
                fontSize = 10.sp,
                fontWeight = FontWeight.SemiBold,
                letterSpacing = 1.sp
            ),
            color = PukaarColors.TextSecondary
        )

        Spacer(modifier = Modifier.height(2.dp))

        Text(
            text = if (unit != null) "$value $unit" else value,
            fontFamily = RajdhaniFontFamily,
            fontWeight = FontWeight.Bold,
            fontSize = 24.sp,
            color = valueColor
        )
    }
}
