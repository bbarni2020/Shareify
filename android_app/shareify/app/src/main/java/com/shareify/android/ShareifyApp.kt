package com.shareify.android

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.shareify.android.ui.screens.HomeScreen
import com.shareify.android.ui.screens.LoginScreen
import com.shareify.android.ui.screens.OnboardingScreen
import com.shareify.android.ui.screens.ServerLoginScreen
import com.shareify.android.ui.screens.SettingsScreen
import com.shareify.android.viewmodel.AppViewModel

@Composable
fun ShareifyApp() {
    val navController = rememberNavController()
    val appViewModel: AppViewModel = viewModel()
    val appState by appViewModel.appState.collectAsState()

    NavHost(
        navController = navController,
        startDestination = if (appState.hasCompletedOnboarding) "login" else "onboarding"
    ) {
        composable("onboarding") {
            OnboardingScreen(
                onOnboardingComplete = {
                    appViewModel.completeOnboarding()
                    navController.navigate("login") {
                        popUpTo("onboarding") { inclusive = true }
                    }
                }
            )
        }
        
        composable("login") {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate("server_login") {
                        popUpTo("login") { inclusive = true }
                    }
                },
                onNavigateToServerLogin = {
                    navController.navigate("server_login")
                }
            )
        }
        
        composable("server_login") {
            ServerLoginScreen(
                onServerLoginSuccess = {
                    navController.navigate("home") {
                        popUpTo("server_login") { inclusive = true }
                    }
                }
            )
        }
        
        composable("home") {
            HomeScreen(
                onNavigateToSettings = {
                    navController.navigate("settings")
                }
            )
        }
        
        composable("settings") {
            SettingsScreen(
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
    }
}