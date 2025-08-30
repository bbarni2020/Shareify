package com.shareify.android.data.model

data class User(
    val id: String,
    val username: String,
    val email: String? = null
)

data class LoginRequest(
    val email: String,
    val password: String
)

data class LoginResponse(
    val token: String,
    val user: User,
    val message: String
)

data class ServerLoginRequest(
    val username: String,
    val password: String
)

data class ServerLoginResponse(
    val token: String,
    val message: String
)

data class FileItem(
    val name: String,
    val type: String, // "file" or "directory"
    val size: Long? = null,
    val lastModified: String? = null,
    val path: String
)

data class ServerInfo(
    val id: String,
    val name: String,
    val url: String,
    val status: String
)

data class ErrorResponse(
    val error: String
)

data class AppState(
    val hasCompletedOnboarding: Boolean = false,
    val isLoggedIn: Boolean = false,
    val currentUser: User? = null,
    val selectedBackground: Int = 1
)