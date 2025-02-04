import SwiftUI

class LiveGameManager: ObservableObject {
    @Published var liveGameInfo: String = ""
    @Published var gameSummary: String = ""
    @Published var isLoading = true
    @Published var showConsole = false
    private let serverURL = "http://localhost:8000"
    
    func checkLiveGames() {
        guard let url = URL(string: "\(serverURL)/live_games/") else { return }
        
        URLSession.shared.dataTask(with: url) { [weak self] data, response, error in
            DispatchQueue.main.async {
                self?.isLoading = false
                if let data = data,
                   let json = try? JSONDecoder().decode([String: String].self, from: data) {
                    self?.liveGameInfo = json["game_info"] ?? "No live games at the moment"
                }
                self?.getGameSummary()
            }
        }.resume()
    }
    
    func getGameSummary() {
        guard let url = URL(string: "\(serverURL)/game_summary/") else { return }
        
        URLSession.shared.dataTask(with: url) { [weak self] data, response, error in
            DispatchQueue.main.async {
                self?.isLoading = false
                if let data = data,
                   let json = try? JSONDecoder().decode([String: String].self, from: data) {
                    self?.gameSummary = json["summary"] ?? "No game summary available"
                }
            }
        }.resume()
    }
}

struct LogoView: View {
    @Environment(\.dismiss) var dismiss
    @State private var isAnimated = false
    @State private var circleScale: CGFloat = 0
    @StateObject private var liveGameManager = LiveGameManager()
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Base background color
                Color.blue.opacity(0.7)
                    .ignoresSafeArea()
                    .opacity(isAnimated ? 1 : 0)
                
                // Expanding circle background
                Circle()
                    .fill(Color.blue.opacity(0.7))
                    .frame(width: 50)
                    .scaleEffect(circleScale)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .ignoresSafeArea()
                
                VStack(spacing: 20) {
                    // Top logo
                    Image("logo")
                        .resizable()
                        .scaledToFit()
                        .frame(width: 120)
                        .padding(.top, 40)
                        .opacity(isAnimated ? 1 : 0)
                        .offset(y: isAnimated ? 0 : -20)
                        .onTapGesture {
                            withAnimation(.spring(response: 0.6, dampingFraction: 0.8)) {
                                isAnimated = false
                            }
                            withAnimation(.easeIn(duration: 0.5).delay(0.2)) {
                                circleScale = 0
                            }
                            DispatchQueue.main.asyncAfter(deadline: .now() + 0.7) {
                                dismiss()
                            }
                        }
                    
                    Spacer()
                    
                    // Center baseball logo
                    Image("baseball2")
                        .resizable()
                        .scaledToFit()
                        .frame(width: 210)
                        .opacity(isAnimated ? 1 : 0)
                        .scaleEffect(isAnimated ? 1 : 0.5)
                        .offset(y: -50)
                        .onTapGesture {
                            withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                                liveGameManager.showConsole.toggle()
                            }
                        }
                    
                    // Live game status
                    HStack(spacing: 8) {
                        if liveGameManager.isLoading {
                            ProgressView()
                                .tint(.white)
                        } else {
                            Circle()
                                .fill(Color.red)
                                .frame(width: 8, height: 8)
                                .opacity(0.8)
                            
                            Text(liveGameManager.liveGameInfo)
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(.white)
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.black.opacity(0.3))
                    .cornerRadius(20)
                    .opacity(isAnimated ? 1 : 0)
                    .offset(y: -30)
                    
                    Spacer()
                }
                
                // Message Console
                if liveGameManager.showConsole {
                    VStack {
                        Spacer()
                        HStack(alignment: .top, spacing: 0) {
                            ScrollView {
                                VStack(alignment: .leading, spacing: 12) {
                                    Text("Live Game Analysis")
                                        .font(.headline)
                                        .foregroundColor(.white)
                                    
                                    if liveGameManager.isLoading {
                                        ProgressView()
                                            .tint(.white)
                                    } else {
                                        Text(liveGameManager.liveGameInfo)
                                            .foregroundColor(.white)
                                            .font(.system(size: 16))
                                        
                                        Divider()
                                            .background(Color.white.opacity(0.3))
                                        
                                        Text("Game Summary")
                                            .font(.headline)
                                            .foregroundColor(.white)
                                        
                                        Text(liveGameManager.gameSummary)
                                            .foregroundColor(.white.opacity(0.8))
                                            .font(.system(size: 14))
                                    }
                                }
                                .padding(.trailing, 12)
                            }
                            
                            // Scroll indicator
                            Rectangle()
                                .fill(Color.white.opacity(0.3))
                                .frame(width: 3)
                                .cornerRadius(1.5)
                                .padding(.trailing, 4)
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 12)
                        .frame(width: UIScreen.main.bounds.width * 0.8) // Make console 80% of screen width
                        .frame(height: 150)
                        .background(Color.black.opacity(0.7))
                        .cornerRadius(15)
                        .padding()
                        .transition(.move(edge: .bottom))
                    }
                    .frame(maxWidth: .infinity) // Center the console
                    .zIndex(1)
                }
            }
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.5)) {
                circleScale = 25
                isAnimated = true
            }
            liveGameManager.checkLiveGames()
        }
    }
}

struct Logo_Previews: PreviewProvider {
    static var previews: some View {
        LogoView()
    }
}

