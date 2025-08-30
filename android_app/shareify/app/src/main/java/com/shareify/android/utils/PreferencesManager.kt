package com.shareify.android.utils

import android.content.Context
import android.content.SharedPreferences

class PreferencesManager(context: Context) {
    
    private val preferences: SharedPreferences = context.getSharedPreferences(
        "shareify_prefs", 
        Context.MODE_PRIVATE
    )
    
    // Onboarding
    fun setOnboardingCompleted(completed: Boolean) {
        preferences.edit().putBoolean(KEY_ONBOARDING_COMPLETED, completed).apply()
    }
    
    fun hasCompletedOnboarding(): Boolean {
        return preferences.getBoolean(KEY_ONBOARDING_COMPLETED, false)
    }
    
    // Background selection
    fun setSelectedBackground(backgroundId: Int) {
        preferences.edit().putInt(KEY_SELECTED_BACKGROUND, backgroundId).apply()
    }
    
    fun getSelectedBackground(): Int {
        return preferences.getInt(KEY_SELECTED_BACKGROUND, 1)
    }
    
    // Theme
    fun setDarkMode(isDarkMode: Boolean) {
        preferences.edit().putBoolean(KEY_DARK_MODE, isDarkMode).apply()
    }
    
    fun isDarkMode(): Boolean {
        return preferences.getBoolean(KEY_DARK_MODE, false)
    }
    
    // Server URL
    fun setLastServerUrl(url: String) {
        preferences.edit().putString(KEY_LAST_SERVER_URL, url).apply()
    }
    
    fun getLastServerUrl(): String? {
        return preferences.getString(KEY_LAST_SERVER_URL, null)
    }
    
    companion object {
        private const val KEY_ONBOARDING_COMPLETED = "onboarding_completed"
        private const val KEY_SELECTED_BACKGROUND = "selected_background"
        private const val KEY_DARK_MODE = "dark_mode"
        private const val KEY_LAST_SERVER_URL = "last_server_url"
    }
}