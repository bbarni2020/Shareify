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
        let pathString = currentPath.joined(separator: "/")
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
                    PreviewView(
                        file: file,
                        content: content,
                        type: type,
                        isLoading: isPreviewLoading,
                        onDismiss: {
                            withAnimation(.easeInOut(duration: 0.35)) {
                                previewedFile = nil
                                previewedFileContent = nil
                                previewedFileType = nil
                            }
                        }
                    )
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
                let newPathString = newPath.joined(separator: "/")
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
                
                let command = "/api/get_file?file_path=\(filePath.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? filePath)"
                let requestBody: [String: Any] = [:]
                
                ServerManager.shared.executeServerCommand(command: command, method: "GET", body: requestBody, waitTime: 5) { result in
                    DispatchQueue.main.async {
                        isPreviewLoading = false
                        switch result {
                        case .success(let response):
                            if let json = response as? [String: Any],
                               let status = json["status"] as? String, status == "File content retrieved" {
                                previewedFileContent = json["content"] as? String
                                previewedFileType = json["type"] as? String
                                
                                withAnimation(.easeInOut(duration: 0.35)) {
                                }
                            } else if let json = response as? [String: Any],
                                      let error = json["error"] as? String {
                                print("Server error: \(error)")
                                previewedFileContent = "Server error: \(error)"
                                previewedFileType = "text"
                            } else {
                                previewedFileContent = "Failed to load file - unexpected response format."
                                previewedFileType = "text"
                            }
                        case .failure(let error):
                            print("Failed to load file: \(error)")
                            previewedFileContent = "Failed to load file: \(error.localizedDescription)"
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
                let newPathString = newPath.joined(separator: "/")
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
    
    @ViewBuilder
    private func filePreviewView(for file: FinderItem, content: String) -> some View {
        let lowerName = file.name.lowercased()
        
        if isImageFile(lowerName) {
            imagePreviewView(file: file, content: content)
        } else if isVideoFile(lowerName) {
            videoPreviewView(file: file, content: content)
        } else if isAudioFile(lowerName) {
            audioPreviewView(file: file, content: content)
        } else if lowerName.hasSuffix(".pdf") {
            pdfPreviewView(file: file, content: content)
        } else if isDocumentFile(lowerName) {
            documentPreviewView(file: file, content: content)
        } else {
            unsupportedFileView(file: file)
        }
    }
    
    private func isImageFile(_ filename: String) -> Bool {
        return filename.hasSuffix(".png") || filename.hasSuffix(".jpg") || filename.hasSuffix(".jpeg") || 
               filename.hasSuffix(".gif") || filename.hasSuffix(".bmp") || filename.hasSuffix(".webp")
    }
    
    private func isVideoFile(_ filename: String) -> Bool {
        return filename.hasSuffix(".mp4") || filename.hasSuffix(".mov") || filename.hasSuffix(".avi") || 
               filename.hasSuffix(".mkv") || filename.hasSuffix(".webm")
    }
    
    private func isAudioFile(_ filename: String) -> Bool {
        return filename.hasSuffix(".mp3") || filename.hasSuffix(".wav") || filename.hasSuffix(".aac") || 
               filename.hasSuffix(".ogg") || filename.hasSuffix(".flac") || filename.hasSuffix(".m4a")
    }
    
    private func isDocumentFile(_ filename: String) -> Bool {
        return filename.hasSuffix(".docx") || filename.hasSuffix(".doc") || filename.hasSuffix(".pptx") || 
               filename.hasSuffix(".xlsx")
    }
    
    @ViewBuilder
    private func imagePreviewView(file: FinderItem, content: String) -> some View {
        if let imageData = Data(base64Encoded: content), let uiImage = UIImage(data: imageData) {
            ScrollView([.horizontal, .vertical]) {
                Image(uiImage: uiImage)
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .padding(28)
            }
        } else {
            VStack {
                Image(systemName: "photo.fill")
                    .font(.system(size: 48))
                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                    .padding(.bottom, 16)
                Text("Failed to decode image.")
                    .font(.system(size: 17))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                    .padding(.horizontal, 28)
                    .padding(.vertical, 16)
            }
        }
    }
    
    @ViewBuilder
    private func videoPreviewView(file: FinderItem, content: String) -> some View {
        if let videoData = Data(base64Encoded: content) {
            let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(file.name)
            if (try? videoData.write(to: tempURL)) != nil {
                VStack {
                    Text("Video File")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                        .padding(.bottom, 20)
                    VideoPlayer(player: AVPlayer(url: tempURL))
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .cornerRadius(12)
                }
                .padding(28)
            } else {
                Text("Failed to write video file for preview.")
                    .font(.system(size: 17))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                    .padding(.horizontal, 28)
                    .padding(.vertical, 16)
            }
        } else {
            VStack {
                Image(systemName: "video.fill")
                    .font(.system(size: 48))
                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                    .padding(.bottom, 16)
                Text("Video file detected but cannot be previewed")
                    .font(.system(size: 17))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 28)
            }
            .padding(.vertical, 40)
        }
    }
    
    @ViewBuilder
    private func audioPreviewView(file: FinderItem, content: String) -> some View {
        if let audioData = Data(base64Encoded: content) {
            let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(file.name)
            if (try? audioData.write(to: tempURL)) != nil {
                VStack {
                    Text("Audio File")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                        .padding(.bottom, 20)
                    VideoPlayer(player: AVPlayer(url: tempURL))
                        .frame(maxWidth: .infinity, maxHeight: 120)
                        .cornerRadius(12)
                }
                .padding(28)
            } else {
                Text("Failed to write audio file for preview.")
                    .font(.system(size: 17))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                    .padding(.horizontal, 28)
                    .padding(.vertical, 16)
            }
        } else {
            VStack {
                Image(systemName: "music.note")
                    .font(.system(size: 48))
                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                    .padding(.bottom, 16)
                Text("Audio file detected but cannot be previewed")
                    .font(.system(size: 17))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 28)
            }
            .padding(.vertical, 40)
        }
    }
    
    @ViewBuilder
    private func pdfPreviewView(file: FinderItem, content: String) -> some View {
        if let pdfData = Data(base64Encoded: content), let pdfDocument = PDFDocument(data: pdfData) {
            VStack {
                Text("PDF Document")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                    .padding(.bottom, 20)
                PDFKitRepresentedView(document: pdfDocument)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .cornerRadius(12)
            }
            .padding(28)
        } else {
            VStack {
                Image(systemName: "doc.fill")
                    .font(.system(size: 48))
                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                    .padding(.bottom, 16)
                Text("Failed to decode PDF.")
                    .font(.system(size: 17))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                    .padding(.horizontal, 28)
                    .padding(.vertical, 16)
            }
        }
    }
    
    @ViewBuilder
    private func documentPreviewView(file: FinderItem, content: String) -> some View {
        if let docData = Data(base64Encoded: content) {
            let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(file.name)
            if (try? docData.write(to: tempURL)) != nil {
                VStack {
                    Text("Document Preview")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                        .padding(.bottom, 20)
                    QuickLookPreview(url: tempURL)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .cornerRadius(12)
                }
                .padding(28)
            } else {
                VStack {
                    Image(systemName: "doc.richtext.fill")
                        .font(.system(size: 48))
                        .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                        .padding(.bottom, 16)
                    Text("Failed to write document file for preview.")
                        .font(.system(size: 17))
                        .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 28)
                        .padding(.vertical, 16)
                }
            }
        } else {
            VStack {
                Image(systemName: "doc.richtext.fill")
                    .font(.system(size: 48))
                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                    .padding(.bottom, 16)
                Text("Failed to decode document file.")
                    .font(.system(size: 17))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 28)
                    .padding(.vertical, 16)
            }
        }
    }
    
    @ViewBuilder
    private func unsupportedFileView(file: FinderItem) -> some View {
        VStack {
            Image(systemName: "doc")
                .font(.system(size: 48))
                .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                .padding(.bottom, 16)
            Text("File Type: \(file.name.components(separatedBy: ".").last?.uppercased() ?? "Unknown")")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                .padding(.bottom, 8)
            Text("Binary file preview not supported.")
                .font(.system(size: 17))
                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                .multilineTextAlignment(.center)
                .padding(.horizontal, 28)
                .padding(.vertical, 16)
        }
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
