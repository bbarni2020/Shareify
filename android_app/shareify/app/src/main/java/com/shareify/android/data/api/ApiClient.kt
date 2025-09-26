package com.shareify.android.data.api

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {
    
    private const val BRIDGE_BASE_URL = "https://bridge.bbarni.hackclub.app/"
    private const val COMMAND_BASE_URL = "https://command.bbarni.hackclub.app/"
    
    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }
    
    private val httpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private val bridgeRetrofit = Retrofit.Builder()
        .baseUrl(BRIDGE_BASE_URL)
        .client(httpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    private val commandRetrofit = Retrofit.Builder()
        .baseUrl(COMMAND_BASE_URL)
        .client(httpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    val bridgeApiService: ShareifyApiService = bridgeRetrofit.create(ShareifyApiService::class.java)
    val commandApiService: CommandApiService = commandRetrofit.create(CommandApiService::class.java)
}