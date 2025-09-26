package com.shareify.android.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.shareify.android.data.model.AppState
import com.shareify.android.data.repository.ShareifyRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.launch

class AppViewModel(application: Application) : AndroidViewModel(application) {
    
    private val repository = ShareifyRepository(application)
    
    val appState: Flow<AppState> = repository.appState
    
    fun completeOnboarding() {
        repository.completeOnboarding()
    }
    
    fun setSelectedBackground(backgroundId: Int) {
        repository.setSelectedBackground(backgroundId)
    }
    
    fun logout() {
        viewModelScope.launch {
            repository.logout()
        }
    }
}