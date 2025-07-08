import SwiftUI

struct FinderItem: Identifiable, Codable {
    let id = UUID()
    let name: String
    let isFolder: Bool
    let size: String?
    let dateModified: String
    
    enum CodingKeys: String, CodingKey {
        case name, isFolder, size, dateModified
    }
}

struct FinderView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var currentPath: [String] = []
    @State private var isGridView = false
    @State private var selectedItems: Set<UUID> = []
    @State private var searchText = ""
    @State private var showingActionSheet = false
    @State private var items: [FinderItem] = []
    @State private var isLoading = false
    @StateObject private var backgroundManager = BackgroundManager.shared
    
    
    var currentItems: [FinderItem] {
        return items
    }
    
    var filteredItems: [FinderItem] {
        if searchText.isEmpty {
            return currentItems
        } else {
            return currentItems.filter { $0.name.localizedCaseInsensitiveContains(searchText) }
        }
    }
    
    func fetchFinderItems() {
        isLoading = true
        let pathString = currentPath.joined(separator: "/")
        
        print("DEBUG: Starting fetchFinderItems() with path: '\(pathString)'")
        
        guard let url = URL(string: "https://command.bbarni.hackclub.app/") else {
            print("DEBUG: Failed to create URL")
            isLoading = false
            return
        }
        
        print("DEBUG: URL created: \(url)")
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        print("DEBUG: Base request configured - Method: POST, Content-Type: application/json")
        
        if let jwtToken = UserDefaults.standard.string(forKey: "jwt_token"), !jwtToken.isEmpty {
            request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
            print("DEBUG: JWT Token added to Authorization header: Bearer \(jwtToken)")
        } else {
            print("DEBUG: No JWT token found in UserDefaults")
        }
        
        if let shareifyJWT = UserDefaults.standard.string(forKey: "shareify_jwt"), !shareifyJWT.isEmpty {
            request.setValue(shareifyJWT, forHTTPHeaderField: "X-Shareify-JWT")
            print("DEBUG: Shareify JWT added to X-Shareify-JWT header: \(shareifyJWT)")
        } else {
            print("DEBUG: No Shareify JWT found in UserDefaults")
        }
        
        let requestBody: [String: Any] = [
            "command": "/finder",
            "method": "GET",
            "body": [
                "path": pathString
            ],
            "wait_time": 3
        ]
        
        print("DEBUG: Request body created: \(requestBody)")
        
        do {
            let httpBodyData = try JSONSerialization.data(withJSONObject: requestBody)
            request.httpBody = httpBodyData
            if let bodyString = String(data: httpBodyData, encoding: .utf8) {
                print("DEBUG: Request body as JSON string: \(bodyString)")
            }
        } catch {
            print("DEBUG: Failed to serialize request body: \(error)")
            isLoading = false
            return
        }
        
        print("DEBUG: Full request headers: \(request.allHTTPHeaderFields ?? [:])")
        print("DEBUG: Starting URLSession data task...")
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            print("DEBUG: URLSession task completed")
            
            if let error = error {
                print("DEBUG: URLSession error: \(error)")
            }
            
            if let httpResponse = response as? HTTPURLResponse {
                print("DEBUG: HTTP response status code: \(httpResponse.statusCode)")
                print("DEBUG: HTTP response headers: \(httpResponse.allHeaderFields)")
            }
            
            if let data = data {
                print("DEBUG: Response data received - \(data.count) bytes")
                if let responseString = String(data: data, encoding: .utf8) {
                    print("DEBUG: Response data as string: \(responseString)")
                }
            } else {
                print("DEBUG: No response data received")
            }
            
            DispatchQueue.main.async {
                isLoading = false
                
                if let data = data {
                    do {
                        let jsonResponse = try JSONSerialization.jsonObject(with: data) as? [String: Any]
                        print("DEBUG: Parsed JSON response: \(jsonResponse ?? [:])")
                        
                        if let fileNames = jsonResponse?["items"] as? [String] {
                            print("DEBUG: Found items array with \(fileNames.count) items: \(fileNames)")
                            let finderItems = fileNames.map { fileName in
                                FinderItem(
                                    name: fileName,
                                    isFolder: !fileName.contains("."),
                                    size: fileName.contains(".") ? "Unknown" : nil,
                                    dateModified: "Recently"
                                )
                            }
                            self.items = finderItems
                            print("DEBUG: Created \(finderItems.count) FinderItem objects")
                        } else {
                            print("DEBUG: No 'items' array found in response or wrong type")
                            self.items = []
                        }
                    } catch {
                        print("DEBUG: Error parsing JSON response: \(error)")
                        self.items = []
                    }
                } else {
                    print("DEBUG: No data to process, setting items to empty array")
                    self.items = []
                }
                
                print("DEBUG: Final items count: \(self.items.count)")
            }
        }.resume()
    }
    
    var body: some View {
        GeometryReader { geometry in
            Image(backgroundManager.backgroundImageName)
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(width: geometry.size.width, height: geometry.size.height)
                .clipped()
                .ignoresSafeArea(.all)
                .overlay(
                    Rectangle()
                        .foregroundColor(.clear)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(.ultraThinMaterial)
                        .colorScheme(.light)
                        .ignoresSafeArea(.all)
                        .overlay(
                            NavigationStack {
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
                    
                    if isLoading {
                        ProgressView()
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                            .background(.clear)
                    }
                                }
                                .padding(.top, 50)
                            }
                            .navigationBarHidden(true)
                        )
                )
        }
        .ignoresSafeArea(.all)
        .onAppear {
            fetchFinderItems()
        }
        .onChange(of: currentPath) {
            fetchFinderItems()
        }
    }
    
    private var topNavigationBar: some View {
        HStack {
            Button(action: {
                if currentPath.count > 0 {
                    withAnimation(.easeInOut(duration: 0.3)) {
                        _ = currentPath.removeLast()
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
        .background(.clear)
        .padding(.horizontal, 20)
        .padding(.top, 15)
    }
    
    private var pathBreadcrumb: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                let displayPath = currentPath.isEmpty ? ["Root"] : currentPath
                ForEach(Array(displayPath.enumerated()), id: \.offset) { index, pathComponent in
                    HStack(spacing: 8) {
                        Button(action: {
                            if currentPath.isEmpty && index == 0 {
                                return
                            }
                            if index < currentPath.count - 1 {
                                withAnimation(.easeInOut(duration: 0.3)) {
                                    let newPath = Array(currentPath.prefix(index + 1))
                                    currentPath = newPath
                                }
                            }
                        }) {
                            Text(pathComponent)
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(index == displayPath.count - 1 ? 
                                               Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255) : 
                                               Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                        }
                        .disabled(index == displayPath.count - 1)
                        
                        if index < displayPath.count - 1 {
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
                    .background(.clear)
            }
            
            Spacer()
            
            Text("\(filteredItems.count) items")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
            
            Spacer()
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
        .background(.clear)
        .onTapGesture {
            if item.isFolder {
                withAnimation(.easeInOut(duration: 0.3)) {
                    currentPath.append(item.name)
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
        .background(.clear)
        .onTapGesture {
            if item.isFolder {
                withAnimation(.easeInOut(duration: 0.3)) {
                    currentPath.append(item.name)
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
