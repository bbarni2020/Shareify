package com.shareify.android.utils

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class SecurePreferences(context: Context) {
    
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()
    
    private val sharedPreferences: SharedPreferences = EncryptedSharedPreferences.create(
        context,
        "shareify_secure_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
    
    // JWT Token storage
    fun saveJwtToken(token: String) {
        sharedPreferences.edit().putString(KEY_JWT_TOKEN, token).apply()
    }
    
    fun getJwtToken(): String? {
        return sharedPreferences.getString(KEY_JWT_TOKEN, null)
    }
    
    fun clearJwtToken() {
        sharedPreferences.edit().remove(KEY_JWT_TOKEN).apply()
    }
    
    // Server credentials
    fun saveServerCredentials(username: String, password: String) {
        sharedPreferences.edit()
            .putString(KEY_SERVER_USERNAME, username)
            .putString(KEY_SERVER_PASSWORD, password)
            .apply()
    }
    
    fun getServerUsername(): String? {
        return sharedPreferences.getString(KEY_SERVER_USERNAME, null)
    }
    
    fun getServerPassword(): String? {
        return sharedPreferences.getString(KEY_SERVER_PASSWORD, null)
    }
    
    fun clearServerCredentials() {
        sharedPreferences.edit()
            .remove(KEY_SERVER_USERNAME)
            .remove(KEY_SERVER_PASSWORD)
            .apply()
    }
    
    // Shareify JWT Token (from server login)
    fun saveShareifyJwt(token: String) {
        sharedPreferences.edit().putString(KEY_SHAREIFY_JWT, token).apply()
    }
    
    fun getShareifyJwt(): String? {
        return sharedPreferences.getString(KEY_SHAREIFY_JWT, null)
    }
    
    fun clearShareifyJwt() {
        sharedPreferences.edit().remove(KEY_SHAREIFY_JWT).apply()
    }
    
    // User info
    fun saveUserId(userId: String) {
        sharedPreferences.edit().putString(KEY_USER_ID, userId).apply()
    }
    
    fun getUserId(): String? {
        return sharedPreferences.getString(KEY_USER_ID, null)
    }
    
    fun saveUsername(username: String) {
        sharedPreferences.edit().putString(KEY_USERNAME, username).apply()
    }
    
    fun getUsername(): String? {
        return sharedPreferences.getString(KEY_USERNAME, null)
    }
    
    fun clearUserInfo() {
        sharedPreferences.edit()
            .remove(KEY_USER_ID)
            .remove(KEY_USERNAME)
            .apply()
    }
    
    // Clear all data
    fun clearAll() {
        sharedPreferences.edit().clear().apply()
    }
    
    companion object {
        private const val KEY_JWT_TOKEN = "jwt_token"
        private const val KEY_SERVER_USERNAME = "server_username"
        private const val KEY_SERVER_PASSWORD = "server_password"
        private const val KEY_SHAREIFY_JWT = "shareify_jwt"
        private const val KEY_USER_ID = "user_id"
        private const val KEY_USERNAME = "username"
    }
}