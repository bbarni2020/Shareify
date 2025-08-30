package com.shareify.android.data.repository

import android.content.Context
import com.shareify.android.data.api.ApiClient
import com.shareify.android.data.api.CommandRequest
import com.shareify.android.data.model.*
import com.shareify.android.utils.PreferencesManager
import com.shareify.android.utils.SecurePreferences
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class ShareifyRepository(context: Context) {
    
    private val securePreferences = SecurePreferences(context)
    private val preferencesManager = PreferencesManager(context)
    
    private val bridgeApi = ApiClient.bridgeApiService
    private val commandApi = ApiClient.commandApiService
    
    private val _appState = MutableStateFlow(
        AppState(
            hasCompletedOnboarding = preferencesManager.hasCompletedOnboarding(),
            selectedBackground = preferencesManager.getSelectedBackground()
        )
    )
    val appState: Flow<AppState> = _appState.asStateFlow()
    
    // Authentication
    suspend fun login(email: String, password: String): Result<LoginResponse> {
        return try {
            val response = bridgeApi.login(LoginRequest(email, password))
            if (response.isSuccessful && response.body() != null) {
                val loginResponse = response.body()!!
                
                // Save tokens securely
                securePreferences.saveJwtToken(loginResponse.token)
                securePreferences.saveUserId(loginResponse.user.id)
                securePreferences.saveUsername(loginResponse.user.username)
                
                updateAppState { it.copy(isLoggedIn = true, currentUser = loginResponse.user) }
                
                Result.success(loginResponse)
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Login failed"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun serverLogin(username: String, password: String): Result<ServerLoginResponse> {
        return try {
            val jwtToken = securePreferences.getJwtToken()
                ?: return Result.failure(Exception("No JWT token found"))
            
            // Use command API to execute server login
            val commandRequest = CommandRequest(
                command = "/user/login",
                method = "POST",
                wait_time = 5,
                body = mapOf(
                    "username" to username,
                    "password" to password
                )
            )
            
            val response = commandApi.executeCommand("Bearer $jwtToken", commandRequest)
            if (response.isSuccessful && response.body() != null) {
                val commandResponse = response.body()!!
                if (commandResponse.success) {
                    // Save server credentials
                    securePreferences.saveServerCredentials(username, password)
                    
                    // Extract token from response if available
                    val data = commandResponse.data as? Map<*, *>
                    val token = data?.get("token") as? String
                    token?.let { securePreferences.saveShareifyJwt(it) }
                    
                    Result.success(ServerLoginResponse(token ?: "", "Server login successful"))
                } else {
                    Result.failure(Exception(commandResponse.error ?: "Server login failed"))
                }
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Server login failed"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun getFiles(path: String = "/"): Result<List<FileItem>> {
        return try {
            val jwtToken = securePreferences.getJwtToken()
                ?: return Result.failure(Exception("No JWT token found"))
            
            val response = bridgeApi.getFiles("Bearer $jwtToken", path)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Failed to get files"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    // App state management
    fun completeOnboarding() {
        preferencesManager.setOnboardingCompleted(true)
        updateAppState { it.copy(hasCompletedOnboarding = true) }
    }
    
    fun setSelectedBackground(backgroundId: Int) {
        preferencesManager.setSelectedBackground(backgroundId)
        updateAppState { it.copy(selectedBackground = backgroundId) }
    }
    
    fun logout() {
        securePreferences.clearAll()
        updateAppState { 
            it.copy(
                isLoggedIn = false,
                currentUser = null
            )
        }
    }
    
    // Token management
    fun hasValidJwtToken(): Boolean {
        return securePreferences.getJwtToken() != null
    }
    
    fun hasServerCredentials(): Boolean {
        return securePreferences.getServerUsername() != null && 
               securePreferences.getServerPassword() != null
    }
    
    private fun updateAppState(update: (AppState) -> AppState) {
        _appState.value = update(_appState.value)
    }
}