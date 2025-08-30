package com.shareify.android.data.api

import com.shareify.android.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface ShareifyApiService {
    
    @POST("login")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>
    
    @POST("/user/login")
    suspend fun serverLogin(
        @Header("Authorization") token: String,
        @Body request: ServerLoginRequest
    ): Response<ServerLoginResponse>
    
    @GET("files")
    suspend fun getFiles(
        @Header("Authorization") token: String,
        @Query("path") path: String = "/"
    ): Response<List<FileItem>>
    
    @GET("servers")
    suspend fun getUserServers(
        @Header("Authorization") token: String
    ): Response<List<ServerInfo>>
}

interface CommandApiService {
    
    @POST("/")
    suspend fun executeCommand(
        @Header("Authorization") token: String,
        @Body command: CommandRequest
    ): Response<CommandResponse>
}

data class CommandRequest(
    val command: String,
    val method: String = "GET",
    val wait_time: Int = 2,
    val body: Map<String, Any> = emptyMap()
)

data class CommandResponse(
    val success: Boolean,
    val data: Any? = null,
    val error: String? = null
)