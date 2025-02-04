import SwiftUI
import AVFoundation

class AudioManager: ObservableObject {
    private var audioRecorder: AVAudioRecorder?
    private var audioPlayer: AVAudioPlayer?
    private var timer: Timer?
    @Published var isDetectingSound = false
    @Published var transcribedText = ""
    @Published var geminiResponse = ""
    private let serverURL = "http://localhost:8000" // Change this to your server URL
    
    func startRecording() {
        setupAudioRecorder()
        print("🎤 Recording started")
    }
    
    func stopRecording() {
        timer?.invalidate()
        audioRecorder?.stop()
        isDetectingSound = false
        print("⏹️ Recording stopped")
        
        // Send the recorded audio to backend
        sendAudioToBackend()
    }
    
    private func sendAudioToBackend() {
        guard let audioURL = audioRecorder?.url else { return }
        
        let request = createUploadRequest(with: audioURL)
        
        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            if let error = error {
                print("❌ Upload error: \(error)")
                return
            }
            
            if let data = data,
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                DispatchQueue.main.async {
                    self?.transcribedText = json["text"] as? String ?? ""
                    self?.geminiResponse = json["gemini_response"] as? String ?? ""
                    
                    // Play the audio response
                    if let audioContent = json["audio_content"] as? String {
                        self?.playAudioResponse(base64Audio: audioContent)
                    }
                    
                    print("🗣️ Transcribed: \(self?.transcribedText ?? "")")
                    print("🤖 Gemini: \(self?.geminiResponse ?? "")")
                }
            }
        }.resume()
    }
    
    private func playAudioResponse(base64Audio: String) {
        guard let audioData = Data(base64Encoded: base64Audio) else {
            print("❌ Failed to decode base64 audio")
            return
        }
        
        do {
            // Configure audio session for playback
            try AVAudioSession.sharedInstance().setCategory(.playback)
            try AVAudioSession.sharedInstance().setActive(true)
            
            // Create and play audio
            audioPlayer = try AVAudioPlayer(data: audioData)
            audioPlayer?.prepareToPlay()
            audioPlayer?.play()
            
            print("🔊 Playing audio response")
        } catch {
            print("❌ Error playing audio: \(error.localizedDescription)")
        }
    }
    
    private func createUploadRequest(with audioURL: URL) -> URLRequest {
        var request = URLRequest(url: URL(string: "\(serverURL)/transcribe/")!)
        request.httpMethod = "POST"
        
        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        var body = Data()
        let audioData = try? Data(contentsOf: audioURL)
        
        // Add audio file to form data
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"audio.wav\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/wav\r\n\r\n".data(using: .utf8)!)
        body.append(audioData ?? Data())
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        
        request.httpBody = body
        return request
    }
    
    private func setupAudioRecorder() {
        let audioSession = AVAudioSession.sharedInstance()
        
        do {
            try audioSession.setCategory(.playAndRecord, mode: .default)
            try audioSession.setActive(true)
            
            let url = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("temp.wav")
            let settings: [String: Any] = [
                AVFormatIDKey: Int(kAudioFormatLinearPCM),
                AVSampleRateKey: 44100.0,
                AVNumberOfChannelsKey: 1,
                AVEncoderAudioQualityKey: AVAudioQuality.min.rawValue
            ]
            
            audioRecorder = try AVAudioRecorder(url: url, settings: settings)
            audioRecorder?.isMeteringEnabled = true
            audioRecorder?.record()
            
            startMonitoring()
        } catch {
            print("❌ Audio recording setup failed: \(error.localizedDescription)")
        }
    }
    
    private func startMonitoring() {
        timer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            self?.audioRecorder?.updateMeters()
            let level = self?.audioRecorder?.averagePower(forChannel: 0) ?? -160
            self?.isDetectingSound = level > -50
            
            //if self?.isDetectingSound == true {
                //print("🔊 Sound detected: \(level) dB")
            //}
        }
    }
    
    deinit {
        stopRecording()
    }
}

struct WaveformBar: View {
    let index: Int
    @State private var height: CGFloat = 0
    
    var body: some View {
        RoundedRectangle(cornerRadius: 2)
            .fill(Color.blue.opacity(0.8))
            .frame(width: 4, height: height)
            .onAppear {
                withAnimation(
                    .easeInOut(duration: 0.5)
                    .repeatForever()
                    .delay(Double(index) * 0.1)
                ) {
                    height = CGFloat.random(in: 10...30)
                }
            }
    }
}

struct ContentView: View {
    @StateObject private var audioManager = AudioManager()
    @State private var isEnlarged = false
    @State private var showLogoDetail = false
    
    var body: some View {
        ZStack {
            // Background color
            Color(hex: "FADE44")
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                // MLB Logo at top
                Image("logo")
                    .resizable()
                    .scaledToFit()
                    .frame(width: 120)
                    .padding(.top, 40)
                    .onTapGesture {
                        showLogoDetail = true
                    }
                    .fullScreenCover(isPresented: $showLogoDetail) {
                        LogoView()
                            .transition(.opacity)
                    }
                
                // Fixed height spacer
                Spacer()
                    .frame(height: 100)
                
                // Baseball and waveform in fixed position
                VStack(spacing: 20) {
                    // Baseball
                    Image("baseball")
                        .resizable()
                        .scaledToFit()
                        .frame(width: isEnlarged ? 350 : 330)
                        .rotationEffect(.degrees(isEnlarged ? 10 : -10))
                        .animation(.spring(response: 0.3, dampingFraction: 0.6), value: isEnlarged)
                        .onTapGesture {
                            isEnlarged.toggle()
                            if isEnlarged {
                                audioManager.startRecording()
                            } else {
                                audioManager.stopRecording()
                            }
                        }
                    
                    // Waveform with fixed height
                    HStack(spacing: 4) {
                        ForEach(0..<20) { index in
                            if isEnlarged && audioManager.isDetectingSound {
                                WaveformBar(index: index)
                            } else {
                                RoundedRectangle(cornerRadius: 2)
                                    .fill(Color.blue.opacity(0.8))
                                    .frame(width: 4, height: 3)
                            }
                        }
                    }
                    .frame(height: 30)
                }
                .frame(height: 400) // Fixed height container for baseball and waveform
                
                // Flexible spacer
                Spacer()
                
                // Responses at bottom
                if !audioManager.transcribedText.isEmpty {
                    VStack(spacing: 8) {
                        Text(audioManager.transcribedText)
                            .font(.system(size: 14))
                            .lineLimit(2)
                            .truncationMode(.tail)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(Color.white.opacity(0.8))
                            .cornerRadius(8)
                        
                        if !audioManager.geminiResponse.isEmpty {
                            Text(audioManager.geminiResponse)
                                .font(.system(size: 14))
                                .lineLimit(2)
                                .truncationMode(.tail)
                                .padding(.horizontal, 16)
                                .padding(.vertical, 8)
                                .background(Color.blue.opacity(0.1))
                                .cornerRadius(8)
                        }
                    }
                    .padding(.horizontal)
                    .padding(.bottom, 30)
                }
            }
        }
    }
}

// Helper extension to use hex colors
extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 0)
        }

        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue:  Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
