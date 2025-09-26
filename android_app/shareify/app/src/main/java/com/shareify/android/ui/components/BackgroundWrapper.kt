package com.shareify.android.ui.components

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.runtime.collectAsState
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.lifecycle.viewmodel.compose.viewModel
import com.shareify.android.viewmodel.AppViewModel

@Composable
fun BackgroundWrapper(
    content: @Composable () -> Unit
) {
    val appViewModel: AppViewModel = viewModel()
    val appState by appViewModel.appState.collectAsState()
    
    Box(modifier = Modifier.fillMaxSize()) {
        // Background gradient as fallback
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    Brush.verticalGradient(
                        colors = listOf(
                            MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f),
                            MaterialTheme.colorScheme.secondaryContainer.copy(alpha = 0.2f),
                            MaterialTheme.colorScheme.tertiaryContainer.copy(alpha = 0.1f)
                        )
                    )
                )
        )
        
        // Try to load background image based on selection
        try {
            val backgroundResource = getBackgroundResource(appState.selectedBackground)
            backgroundResource?.let { resource ->
                Image(
                    painter = painterResource(id = resource),
                    contentDescription = "Background",
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop,
                    alpha = 0.8f
                )
            }
        } catch (e: Exception) {
            // Fallback to gradient if image loading fails
        }
        
        // Semi-transparent overlay for better text readability
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    MaterialTheme.colorScheme.surface.copy(alpha = 0.1f)
                )
        )
        
        // Content
        content()
    }
}

private fun getBackgroundResource(backgroundId: Int): Int? {
    // Map background IDs to drawable resources
    // For now, return null until we add actual background images
    return when (backgroundId) {
        in 1..19 -> null // Would map to actual drawable resources
        else -> null
    }
}