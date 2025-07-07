import SwiftUI

struct FinderItem: Identifiable {
    let id = UUID()
    let name: String
    let isFolder: Bool
    let size: String?
    let dateModified: String
}

struct FinderView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var currentPath: [String] = ["Home"]
    @State private var isGridView = false
    @State private var selectedItems: Set<UUID> = []
    @State private var searchText = ""
    @State private var showingActionSheet = false
    @StateObject private var backgroundManager = BackgroundManager.shared
    
    let dummyItems: [String: [FinderItem]] = [
        "Home": [
            FinderItem(name: "Documents", isFolder: true, size: nil, dateModified: "Today, 2:30 PM"),
            FinderItem(name: "Downloads", isFolder: true, size: nil, dateModified: "Yesterday, 4:15 PM"),
            FinderItem(name: "Pictures", isFolder: true, size: nil, dateModified: "Jan 15, 2025"),
            FinderItem(name: "Movies", isFolder: true, size: nil, dateModified: "Jan 10, 2025"),
            FinderItem(name: "Music", isFolder: true, size: nil, dateModified: "Dec 28, 2024"),
            FinderItem(name: "Project Report.pdf", isFolder: false, size: "2.3 MB", dateModified: "Today, 1:45 PM"),
            FinderItem(name: "Presentation.pptx", isFolder: false, size: "15.7 MB", dateModified: "Yesterday, 9:20 AM")
        ],
        "Documents": [
            FinderItem(name: "Work", isFolder: true, size: nil, dateModified: "Today, 10:30 AM"),
            FinderItem(name: "Personal", isFolder: true, size: nil, dateModified: "Yesterday, 2:15 PM"),
            FinderItem(name: "Resume.pdf", isFolder: false, size: "1.2 MB", dateModified: "Jan 22, 2025"),
            FinderItem(name: "Contract.docx", isFolder: false, size: "456 KB", dateModified: "Jan 20, 2025"),
            FinderItem(name: "Budget.xlsx", isFolder: false, size: "234 KB", dateModified: "Jan 18, 2025")
        ],
        "Downloads": [
            FinderItem(name: "Software", isFolder: true, size: nil, dateModified: "Jan 15, 2025"),
            FinderItem(name: "Images", isFolder: true, size: nil, dateModified: "Jan 12, 2025"),
            FinderItem(name: "Setup.dmg", isFolder: false, size: "89 MB", dateModified: "Today, 3:20 PM"),
            FinderItem(name: "Archive.zip", isFolder: false, size: "12 MB", dateModified: "Yesterday, 11:45 AM"),
            FinderItem(name: "Document.pdf", isFolder: false, size: "3.4 MB", dateModified: "Jan 19, 2025")
        ],
        "Pictures": [
            FinderItem(name: "Vacation 2025", isFolder: true, size: nil, dateModified: "Jan 10, 2025"),
            FinderItem(name: "Screenshots", isFolder: true, size: nil, dateModified: "Today, 9:15 AM"),
            FinderItem(name: "Photo1.jpg", isFolder: false, size: "5.2 MB", dateModified: "Jan 16, 2025"),
            FinderItem(name: "Photo2.jpg", isFolder: false, size: "4.8 MB", dateModified: "Jan 16, 2025"),
            FinderItem(name: "Portrait.png", isFolder: false, size: "2.1 MB", dateModified: "Jan 14, 2025")
        ]
    ]
    
    var currentItems: [FinderItem] {
        let currentFolder = currentPath.last ?? "Home"
        return dummyItems[currentFolder] ?? []
    }
    
    var filteredItems: [FinderItem] {
        if searchText.isEmpty {
            return currentItems
        } else {
            return currentItems.filter { $0.name.localizedCaseInsensitiveContains(searchText) }
        }
    }
    
    var body: some View {
        NavigationStack {
            GeometryReader { geometry in
                Image(backgroundManager.backgroundImageName)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: geometry.size.width, height: geometry.size.height)
                    .clipped()
                    .ignoresSafeArea(.all)
                    .overlay(
                        VStack(spacing: 0) {
                            topNavigationBar
                            
                            searchBar
                            
                            pathBreadcrumb
                            
                            toolBar
                            
                            if isGridView {
                                gridView
                            } else {
                                listView
                            }
                        }
                    )
            }
        }
        .navigationBarHidden(true)
    }
    
    private var topNavigationBar: some View {
        HStack {
            Button(action: {
                if currentPath.count > 1 {
                    withAnimation(.easeInOut(duration: 0.3)) {
                        currentPath.removeLast()
                    }
                } else {
                    dismiss()
                }
            }) {
                Image(systemName: "chevron.left")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            }
            
            Spacer()
            
            Text("Finder")
                .font(.system(size: 20, weight: .bold))
                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            
            Spacer()
            
            Button(action: {
                showingActionSheet = true
            }) {
                Image(systemName: "ellipsis")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            }
        }
        .padding(.horizontal, 20)
        .padding(.top, 10)
        .confirmationDialog("Options", isPresented: $showingActionSheet, titleVisibility: .visible) {
            Button("Create Folder") { }
            Button("Import Files") { }
            Button("Select All") { }
            Button("Cancel", role: .cancel) { }
        }
    }
    
    private var searchBar: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                .font(.system(size: 16))
            
            TextField("Search files and folders", text: $searchText)
                .font(.system(size: 16))
                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
        .colorScheme(.light)
        .padding(.horizontal, 20)
        .padding(.top, 15)
    }
    
    private var pathBreadcrumb: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(Array(currentPath.enumerated()), id: \.offset) { index, pathComponent in
                    HStack(spacing: 8) {
                        Button(action: {
                            if index < currentPath.count - 1 {
                                withAnimation(.easeInOut(duration: 0.3)) {
                                    let newPath = Array(currentPath.prefix(index + 1))
                                    currentPath = newPath
                                }
                            }
                        }) {
                            Text(pathComponent)
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(index == currentPath.count - 1 ? 
                                               Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255) : 
                                               Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                        }
                        .disabled(index == currentPath.count - 1)
                        
                        if index < currentPath.count - 1 {
                            Image(systemName: "chevron.right")
                                .font(.system(size: 12))
                                .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                        }
                    }
                }
            }
            .padding(.horizontal, 20)
        }
        .padding(.top, 12)
    }
    
    private var toolBar: some View {
        HStack {
            Button(action: {
                withAnimation(.easeInOut(duration: 0.3)) {
                    isGridView.toggle()
                }
            }) {
                Image(systemName: isGridView ? "list.bullet" : "square.grid.2x2")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                    .frame(width: 44, height: 44)
                    .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
                    .colorScheme(.light)
            }
            
            Spacer()
            
            Text("\(filteredItems.count) items")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
            
            Spacer()
            
            Button(action: {}) {
                Image(systemName: "arrow.up.arrow.down")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                    .frame(width: 44, height: 44)
                    .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
                    .colorScheme(.light)
            }
        }
        .padding(.horizontal, 20)
        .padding(.top, 15)
    }
    
    private var listView: some View {
        ScrollView {
            LazyVStack(spacing: 8) {
                ForEach(filteredItems) { item in
                    listItemView(item: item)
                }
            }
            .padding(.horizontal, 20)
            .padding(.top, 15)
        }
    }
    
    private var gridView: some View {
        ScrollView {
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 12), count: 3), spacing: 12) {
                ForEach(filteredItems) { item in
                    gridItemView(item: item)
                }
            }
            .padding(.horizontal, 20)
            .padding(.top, 15)
        }
    }
    
    private func listItemView(item: FinderItem) -> some View {
        HStack(spacing: 12) {
            Image(systemName: item.isFolder ? "folder.fill" : fileIcon(for: item.name))
                .font(.system(size: 24))
                .foregroundColor(item.isFolder ? Color.blue : Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                .frame(width: 32, height: 32)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(item.name)
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                    .lineLimit(1)
                
                HStack(spacing: 4) {
                    if let size = item.size {
                        Text(size)
                            .font(.system(size: 12))
                            .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                        
                        Text("•")
                            .font(.system(size: 12))
                            .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                    }
                    
                    Text(item.dateModified)
                        .font(.system(size: 12))
                        .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                }
            }
            
            Spacer()
            
            Button(action: {}) {
                Image(systemName: "ellipsis")
                    .font(.system(size: 16))
                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
        .colorScheme(.light)
        .onTapGesture {
            if item.isFolder {
                let hasContent = dummyItems.keys.contains(item.name)
                if hasContent {
                    withAnimation(.easeInOut(duration: 0.3)) {
                        currentPath.append(item.name)
                    }
                }
            }
        }
    }
    
    private func gridItemView(item: FinderItem) -> some View {
        VStack(spacing: 8) {
            Image(systemName: item.isFolder ? "folder.fill" : fileIcon(for: item.name))
                .font(.system(size: 32))
                .foregroundColor(item.isFolder ? Color.blue : Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                .frame(height: 40)
            
            Text(item.name)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                .lineLimit(2)
                .multilineTextAlignment(.center)
            
            if let size = item.size {
                Text(size)
                    .font(.system(size: 10))
                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.horizontal, 8)
        .padding(.vertical, 12)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
        .colorScheme(.light)
        .onTapGesture {
            if item.isFolder {
                let hasContent = dummyItems.keys.contains(item.name)
                if hasContent {
                    withAnimation(.easeInOut(duration: 0.3)) {
                        currentPath.append(item.name)
                    }
                }
            }
        }
    }
    
    private func fileIcon(for filename: String) -> String {
        let lowercased = filename.lowercased()
        
        if lowercased.hasSuffix(".pdf") {
            return "doc.fill"
        } else if lowercased.hasSuffix(".jpg") || lowercased.hasSuffix(".jpeg") || lowercased.hasSuffix(".png") {
            return "photo.fill"
        } else if lowercased.hasSuffix(".mp4") || lowercased.hasSuffix(".mov") {
            return "video.fill"
        } else if lowercased.hasSuffix(".mp3") || lowercased.hasSuffix(".wav") {
            return "music.note"
        } else if lowercased.hasSuffix(".zip") || lowercased.hasSuffix(".rar") {
            return "archivebox.fill"
        } else if lowercased.hasSuffix(".txt") {
            return "doc.text.fill"
        } else if lowercased.hasSuffix(".pptx") || lowercased.hasSuffix(".ppt") {
            return "doc.richtext.fill"
        } else if lowercased.hasSuffix(".xlsx") || lowercased.hasSuffix(".xls") {
            return "tablecells.fill"
        } else {
            return "doc.fill"
        }
    }
}

#Preview {
    FinderView()
}
