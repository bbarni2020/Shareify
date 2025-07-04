import SwiftUI
import Foundation

class BackgroundManager: ObservableObject {
    @Published var selectedBackground: Int = 1
    
    static let shared = BackgroundManager()
    
    private init() {
        loadSelectedBackground()
    }
    
    private func loadSelectedBackground() {
        selectedBackground = UserDefaults.standard.integer(forKey: "selected_background")
        if selectedBackground == 0 {
            selectedBackground = 1
        }
    }
    
    func saveSelectedBackground(_ background: Int) {
        selectedBackground = background
        UserDefaults.standard.set(background, forKey: "selected_background")
        UserDefaults.standard.synchronize()
    }
    
    var backgroundImageName: String {
        return "back\(selectedBackground)"
    }
}
