import SwiftUI
import PDFKit
import AVKit
import QuickLook

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
    @State private var folderCache: [String: [FinderItem]] = [:] {
        didSet {
            saveFolderCache()
        }
    }
    @State private var previewedFile: FinderItem? = nil
    @State private var previewedFileContent: String? = nil
    @State private var previewedFileType: String? = nil
    @State private var isPreviewLoading: Bool = false
    
    
    var currentItems: [FinderItem] {
        items
    }
    
    var filteredItems: [FinderItem] {
        if searchText.isEmpty {
            return currentItems
        } else {
            return currentItems.filter { $0.name.localizedCaseInsensitiveContains(searchText) }
        }
    }
    
    func fetchFinderItems() {
        let pathString = currentPath.map { "\($0)" }.joined()
        let requestBody: [String: Any] = [
            "path": pathString
        ]
        if let cachedItems = getCachedItems(for: pathString) {
            self.items = cachedItems
        } else {
            self.items = []
        }
        isLoading = true
        ServerManager.shared.executeServerCommand(command: "/finder", method: "GET", body: requestBody, waitTime: 3) { result in
            DispatchQueue.main.async {
                self.isLoading = false
                switch result {
                case .success(let response):
                    var fileNames: [String] = []
                    if let responseDict = response as? [String: Any],
                       let items = responseDict["items"] as? [String] {
                        fileNames = items
                    } else if let directArray = response as? [String] {
                        fileNames = directArray
                    }
                    let finderItems = fileNames.map { fileName in
                        FinderItem(
                            name: fileName,
                            isFolder: !fileName.contains("."),
                            size: fileName.contains(".") ? "Unknown" : nil,
                            dateModified: "Recently"
                        )
                    }
                    self.items = finderItems
                    self.cacheItems(finderItems, for: pathString)
                case .failure(_):
                    self.items = []
                }
            }
        }
    }
    
    private func getCachedItems(for path: String) -> [FinderItem]? {
        return folderCache[path]
    }

    private func cacheItems(_ items: [FinderItem], for path: String) {
        folderCache[path] = items
    }

    private func saveFolderCache() {
        do {
            let data = try JSONEncoder().encode(folderCache)
            UserDefaults.standard.set(data, forKey: "FinderFolderCache")
        } catch {
            print("Failed to save folder cache:", error)
        }
    }

    private func loadFolderCache() {
        if let data = UserDefaults.standard.data(forKey: "FinderFolderCache") {
            do {
                let cache = try JSONDecoder().decode([String: [FinderItem]].self, from: data)
                folderCache = cache
            } catch {
                print("Failed to load folder cache:", error)
            }
        }
    }
    
    private func refreshCurrentFolder() {
        let pathString = currentPath.joined(separator: "/")
        folderCache.removeValue(forKey: pathString)
        fetchFinderItems()
    }
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                Image(backgroundManager.backgroundImageName)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: geometry.size.width, height: geometry.size.height)
                    .clipped()
                    .ignoresSafeArea(.all)
                    .overlay(
                        backgroundManager.backgroundImageName.isEmpty ?
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
                        :
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
                if let file = previewedFile, let content = previewedFileContent, let type = previewedFileType {
                    Color.black.opacity(0.15)
                        .ignoresSafeArea()
                        .transition(.opacity)
                    VStack {
                        HStack {
                            Text(file.name)
                                .font(.system(size: 20, weight: .bold))
                                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                            Spacer()
                            Button(action: {
                                withAnimation(.easeInOut(duration: 0.35)) {
                                    previewedFile = nil
                                    previewedFileContent = nil
                                    previewedFileType = nil
                                }
                            }) {
                                Image(systemName: "xmark.circle.fill")
                                    .font(.system(size: 32))
                                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                            }
                        }
                        .padding(.horizontal, 28)
                        .padding(.top, 70)
                        if isPreviewLoading {
                            ProgressView()
                                .frame(maxWidth: .infinity, maxHeight: .infinity)
                        } else if type == "text" {
                            ScrollView(.vertical) {
                                Text(content)
                                    .font(.system(size: 17))
                                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                    .padding(.horizontal, 28)
                                    .padding(.vertical, 16)
                            }
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                        } else if type == "binary" {
                            let lowerName = file.name.lowercased()
                            AnyView(
                                lowerName.hasSuffix(".png") || lowerName.hasSuffix(".jpg") || lowerName.hasSuffix(".jpeg") ?
                                    (
                                        ( (Data(base64Encoded: content).flatMap { UIImage(data: $0) }) != nil ) ?
                                            AnyView(
                                                Image(uiImage: UIImage(data: Data(base64Encoded: content)!)!)
                                                    .resizable()
                                                    .aspectRatio(contentMode: .fit)
                                                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                                                    .padding(28)
                                            )
                                            :
                                            AnyView(
                                                Text("Failed to decode image.")
                                                    .font(.system(size: 17))
                                                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                                    .padding(.horizontal, 28)
                                                    .padding(.vertical, 16)
                                            )
                                    )
                                : lowerName.hasSuffix(".mp4") || lowerName.hasSuffix(".mov") ?
                                    (
                                        (Data(base64Encoded: content) != nil) ?
                                            (
                                                {
                                                    let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(file.name)
                                                    do {
                                                        try Data(base64Encoded: content)!.write(to: tempURL)
                                                        return AnyView(
                                                            VideoPlayer(player: AVPlayer(url: tempURL))
                                                                .frame(maxWidth: .infinity, maxHeight: .infinity)
                                                                .padding(28)
                                                        )
                                                    } catch {
                                                        return AnyView(
                                                            Text("Failed to write video file for preview.")
                                                                .font(.system(size: 17))
                                                                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                                                .padding(.horizontal, 28)
                                                                .padding(.vertical, 16)
                                                        )
                                                    }
                                                }()
                                            )
                                            :
                                            AnyView(
                                                Text("Failed to decode video.")
                                                    .font(.system(size: 17))
                                                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                                    .padding(.horizontal, 28)
                                                    .padding(.vertical, 16)
                                            )
                                    )
                                : lowerName.hasSuffix(".mp3") || lowerName.hasSuffix(".wav") ?
                                    (
                                        (Data(base64Encoded: content) != nil) ?
                                            (
                                                {
                                                    let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(file.name)
                                                    do {
                                                        try Data(base64Encoded: content)!.write(to: tempURL)
                                                        return AnyView(
                                                            VideoPlayer(player: AVPlayer(url: tempURL))
                                                                .frame(maxWidth: .infinity, maxHeight: 100)
                                                                .padding(28)
                                                        )
                                                    } catch {
                                                        return AnyView(
                                                            Text("Failed to write audio file for preview.")
                                                                .font(.system(size: 17))
                                                                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                                                .padding(.horizontal, 28)
                                                                .padding(.vertical, 16)
                                                        )
                                                    }
                                                }()
                                            )
                                            :
                                            AnyView(
                                                Text("Failed to decode audio.")
                                                    .font(.system(size: 17))
                                                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                                    .padding(.horizontal, 28)
                                                    .padding(.vertical, 16)
                                            )
                                    )
                                : lowerName.hasSuffix(".pdf") ?
                                    (
                                        (Data(base64Encoded: content) != nil && PDFDocument(data: Data(base64Encoded: content)!) != nil) ?
                                            AnyView(
                                                PDFKitRepresentedView(document: PDFDocument(data: Data(base64Encoded: content)!)!)
                                                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                                                    .padding(28)
                                            )
                                            :
                                            AnyView(
                                                Text("Failed to decode PDF.")
                                                    .font(.system(size: 17))
                                                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                                    .padding(.horizontal, 28)
                                                    .padding(.vertical, 16)
                                            )
                                    )
                                : lowerName.hasSuffix(".docx") ?
                                    (
                                        (Data(base64Encoded: content) != nil) ?
                                            (
                                                {
                                                    let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(file.name)
                                                    do {
                                                        try Data(base64Encoded: content)!.write(to: tempURL)
                                                        return AnyView(
                                                            QuickLookPreview(url: tempURL)
                                                                .frame(maxWidth: .infinity, maxHeight: .infinity)
                                                                .padding(28)
                                                        )
                                                    } catch {
                                                        return AnyView(
                                                            Text("Failed to write DOCX file for preview.")
                                                                .font(.system(size: 17))
                                                                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                                                .padding(.horizontal, 28)
                                                                .padding(.vertical, 16)
                                                        )
                                                    }
                                                }()
                                            )
                                            :
                                            AnyView(
                                                Text("Failed to decode DOCX file.")
                                                    .font(.system(size: 17))
                                                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                                    .padding(.horizontal, 28)
                                                    .padding(.vertical, 16)
                                            )
                                    )
                                :
                                    AnyView(
                                        Text("Binary file preview not supported.")
                                            .font(.system(size: 17))
                                            .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                            .padding(.horizontal, 28)
                                            .padding(.vertical, 16)
                                    )
                            )
                        }

                        Spacer()
                    }
                    .frame(width: geometry.size.width, height: geometry.size.height)
                    .background(.ultraThinMaterial)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
                }
            }
        }
        .ignoresSafeArea(.all)
        .onAppear {
            loadFolderCache()
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
            Button("Refresh") { refreshCurrentFolder() }
            Button("Clear Cache") { 
                folderCache.removeAll()
                fetchFinderItems()
            }
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
                    if item.dateModified != "Unknown" {
                        Text(item.dateModified)
                            .font(.system(size: 12))
                            .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                    }
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
                let newPath = currentPath + [item.name]
                let newPathString = newPath.map { "\($0)" }.joined()
                let requestBody: [String: Any] = [
                    "path": newPathString
                ]
                if let cachedItems = getCachedItems(for: newPathString) {
                    self.items = cachedItems
                } else {
                    self.items = []
                }
                isLoading = true
                withAnimation(.easeInOut(duration: 0.3)) {
                    currentPath.append(item.name)
                }
                ServerManager.shared.executeServerCommand(command: "/finder", method: "GET", body: requestBody, waitTime: 3) { result in
                    DispatchQueue.main.async {
                        self.isLoading = false
                        switch result {
                        case .success(let response):
                            var fileNames: [String] = []
                            if let responseDict = response as? [String: Any],
                               let items = responseDict["items"] as? [String] {
                                fileNames = items
                            } else if let directArray = response as? [String] {
                                fileNames = directArray
                            }
                            let finderItems = fileNames.map { fileName in
                                FinderItem(
                                    name: fileName,
                                    isFolder: !fileName.contains("."),
                                    size: fileName.contains(".") ? "Unknown" : nil,
                                    dateModified: "Recently"
                                )
                            }
                            self.items = finderItems
                            self.cacheItems(finderItems, for: newPathString)
                        case .failure(_):
                            self.items = []
                        }
                    }
                }
            } else {
                isPreviewLoading = true
                previewedFile = item
                previewedFileContent = nil
                previewedFileType = nil
                let filePath = (currentPath + [item.name]).joined(separator: "/")
                let requestBody: [String: Any] = [
                    "file_path": filePath
                ]
                ServerManager.shared.executeServerCommand(command: "/get_file", method: "GET", body: requestBody, waitTime: 3) { result in
                    DispatchQueue.main.async {
                        isPreviewLoading = false
                        switch result {
                        case .success(let response):
                            if let json = response as? [String: Any],
                               let status = json["status"] as? String, status == "File content retrieved" {
                                previewedFileContent = json["content"] as? String
                                previewedFileType = json["type"] as? String
                            } else {
                                previewedFileContent = "Failed to load file."
                                previewedFileType = "text"
                            }
                        case .failure(_):
                            previewedFileContent = "Failed to load file."
                            previewedFileType = "text"
                        }
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
        .background(.clear)
        .onTapGesture {
            if item.isFolder {
                let newPath = currentPath + [item.name]
                let newPathString = newPath.map { "\($0)" }.joined()
                let requestBody: [String: Any] = [
                    "path": newPathString
                ]
                if let cachedItems = getCachedItems(for: newPathString) {
                    self.items = cachedItems
                } else {
                    self.items = []
                }
                isLoading = true
                withAnimation(.easeInOut(duration: 0.3)) {
                    currentPath.append(item.name)
                }
                ServerManager.shared.executeServerCommand(command: "/finder", method: "GET", body: requestBody, waitTime: 3) { result in
                    DispatchQueue.main.async {
                        self.isLoading = false
                        switch result {
                        case .success(let response):
                            var fileNames: [String] = []
                            if let responseDict = response as? [String: Any],
                               let items = responseDict["items"] as? [String] {
                                fileNames = items
                            } else if let directArray = response as? [String] {
                                fileNames = directArray
                            }
                            let finderItems = fileNames.map { fileName in
                                FinderItem(
                                    name: fileName,
                                    isFolder: !fileName.contains("."),
                                    size: fileName.contains(".") ? "Unknown" : nil,
                                    dateModified: "Recently"
                                )
                            }
                            self.items = finderItems
                            self.cacheItems(finderItems, for: newPathString)
                        case .failure(_):
                            self.items = []
                        }
                    }
                }
            }
        }
    }
    
    private func fileIcon(for filename: String) -> String {
        let lowercased = filename.lowercased()
        
        if lowercased.hasSuffix(".pdf") {
            return "doc.fill"
        }

        if lowercased.hasSuffix(".jpg") || lowercased.hasSuffix(".jpeg") || lowercased.hasSuffix(".png") || lowercased.hasSuffix(".gif") || lowercased.hasSuffix(".bmp") || lowercased.hasSuffix(".tiff") || lowercased.hasSuffix(".webp") || lowercased.hasSuffix(".svg") || lowercased.hasSuffix(".ico") {
            return "photo.fill"
        }

        if lowercased.hasSuffix(".mp4") || lowercased.hasSuffix(".mov") || lowercased.hasSuffix(".avi") || lowercased.hasSuffix(".wmv") || lowercased.hasSuffix(".flv") || lowercased.hasSuffix(".mkv") || lowercased.hasSuffix(".webm") || lowercased.hasSuffix(".mpeg") || lowercased.hasSuffix(".mpg") || lowercased.hasSuffix(".m4v") {
            return "video.fill"
        }

        if lowercased.hasSuffix(".mp3") || lowercased.hasSuffix(".wav") || lowercased.hasSuffix(".aac") || lowercased.hasSuffix(".ogg") || lowercased.hasSuffix(".flac") || lowercased.hasSuffix(".wma") || lowercased.hasSuffix(".m4a") || lowercased.hasSuffix(".aiff") || lowercased.hasSuffix(".alac") {
            return "music.note"
        }

        if lowercased.hasSuffix(".zip") || lowercased.hasSuffix(".rar") || lowercased.hasSuffix(".7z") || lowercased.hasSuffix(".tar") || lowercased.hasSuffix(".gz") || lowercased.hasSuffix(".bz2") {
            return "archivebox.fill"
        }

        if lowercased.hasSuffix(".txt") || lowercased.hasSuffix(".md") || lowercased.hasSuffix(".rtf") || lowercased.hasSuffix(".csv") || lowercased.hasSuffix(".log") {
            return "doc.text.fill"
        }

        if lowercased.hasSuffix(".pptx") || lowercased.hasSuffix(".ppt") || lowercased.hasSuffix(".odp") {
            return "doc.richtext.fill"
        }

        if lowercased.hasSuffix(".xlsx") || lowercased.hasSuffix(".xls") || lowercased.hasSuffix(".ods") {
            return "tablecells.fill"
        }

        return "doc"
    }
}

struct PDFKitRepresentedView: UIViewRepresentable {
    let document: PDFDocument
    func makeUIView(context: Context) -> PDFView {
        let pdfView = PDFView()
        pdfView.document = document
        pdfView.autoScales = true
        pdfView.backgroundColor = .clear
        return pdfView
    }
    func updateUIView(_ uiView: PDFView, context: Context) {}
}

struct QuickLookPreview: UIViewControllerRepresentable {
    let url: URL
    func makeUIViewController(context: Context) -> QLPreviewController {
        let controller = QLPreviewController()
        controller.dataSource = context.coordinator
        return controller
    }
    func updateUIViewController(_ uiViewController: QLPreviewController, context: Context) {}
    func makeCoordinator() -> Coordinator {
        Coordinator(url: url)
    }
    class Coordinator: NSObject, QLPreviewControllerDataSource {
        let url: URL
        init(url: URL) { self.url = url }
        func numberOfPreviewItems(in controller: QLPreviewController) -> Int { 1 }
        func previewController(_ controller: QLPreviewController, previewItemAt index: Int) -> QLPreviewItem {
            url as QLPreviewItem
        }
    }
}

#Preview {
    FinderView()
}
