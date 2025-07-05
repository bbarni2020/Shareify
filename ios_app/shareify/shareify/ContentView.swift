//
//  ContentView.swift
//  shareify
//
//  Created by Balogh Barnabás on 2025. 06. 26..
//

import SwiftUI

struct ContentView: View {
    @AppStorage("hasCompletedOnboarding") private var hasCompletedOnboarding = false
    
    var body: some View {
        if hasCompletedOnboarding {
            Login()
        } else {
            OnboardingView(isOnboardingComplete: $hasCompletedOnboarding)
        }
    }
}

#Preview {
    ContentView()
}
