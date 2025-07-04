//
//  ContentView.swift
//  shareify
//
//  Created by Balogh Barnabás on 2025. 06. 26..
//

import SwiftUI

struct ContentView: View {
    @State private var hasCompletedOnboarding = UserDefaults.standard.bool(forKey: "hasCompletedOnboarding")
    
    var body: some View {
        if hasCompletedOnboarding {
            Login()
        } else {
            OnboardingView(isOnboardingComplete: $hasCompletedOnboarding)
                .onChange(of: hasCompletedOnboarding) { newValue in
                    if newValue {
                        UserDefaults.standard.set(true, forKey: "hasCompletedOnboarding")
                        UserDefaults.standard.synchronize()
                    }
                }
        }
    }
}

#Preview {
    ContentView()
}
