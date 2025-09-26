package com.shareify.android.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkColorScheme = darkColorScheme(
    primary = Color(0xFFB6CBFF),
    onPrimary = Color(0xFF002962),
    primaryContainer = Color(0xFF0040A3),
    onPrimaryContainer = Color(0xFFDDE7FF),
    secondary = Color(0xFFC2C5DD),
    onSecondary = Color(0xFF2C2F42),
    secondaryContainer = Color(0xFF424559),
    onSecondaryContainer = Color(0xFFDEE1F9),
    tertiary = Color(0xFFE2BBD7),
    onTertiary = Color(0xFF43263E),
    tertiaryContainer = Color(0xFF5B3D56),
    onTertiaryContainer = Color(0xFFFFD7F3),
    error = Color(0xFFFFB4AB),
    onError = Color(0xFF690005),
    errorContainer = Color(0xFF93000A),
    onErrorContainer = Color(0xFFFFDAD6),
    outline = Color(0xFF8E9199),
    outlineVariant = Color(0xFF44474F),
    surface = Color(0xFF101114),
    onSurface = Color(0xFFE2E2E9),
    surfaceVariant = Color(0xFF44474F),
    onSurfaceVariant = Color(0xFFC4C6D0),
    inverseSurface = Color(0xFFE2E2E9),
    inverseOnSurface = Color(0xFF2E3135),
    inversePrimary = Color(0xFF296DE0)
)

private val LightColorScheme = lightColorScheme(
    primary = Color(0xFF3B82F6),
    onPrimary = Color(0xFFFFFFFF),
    primaryContainer = Color(0xFFDDE7FF),
    onPrimaryContainer = Color(0xFF001848),
    secondary = Color(0xFF5A5D72),
    onSecondary = Color(0xFFFFFFFF),
    secondaryContainer = Color(0xFFDEE1F9),
    onSecondaryContainer = Color(0xFF171B2C),
    tertiary = Color(0xFF76546E),
    onTertiary = Color(0xFFFFFFFF),
    tertiaryContainer = Color(0xFFFFD7F3),
    onTertiaryContainer = Color(0xFF2D1228),
    error = Color(0xFFBA1A1A),
    onError = Color(0xFFFFFFFF),
    errorContainer = Color(0xFFFFDAD6),
    onErrorContainer = Color(0xFF410002),
    outline = Color(0xFF74777F),
    outlineVariant = Color(0xFFC4C6D0),
    surface = Color(0xFFF9F9FF),
    onSurface = Color(0xFF191C20),
    surfaceVariant = Color(0xFFE1E2EC),
    onSurfaceVariant = Color(0xFF44474F),
    inverseSurface = Color(0xFF2E3135),
    inverseOnSurface = Color(0xFFF0F0F7),
    inversePrimary = Color(0xFFB6CBFF)
)

@Composable
fun ShareifyTheme(
    darkTheme: Boolean = androidx.compose.foundation.isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}