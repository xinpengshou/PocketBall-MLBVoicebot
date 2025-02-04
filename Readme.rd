# PocketBall - MLBVoiceBot

## Overview
An innovative iOS application that combines real-time MLB game tracking with an AI-powered baseball assistant. The app features live play-by-play updates, chronological game summaries, and a voice-interactive baseball knowledge system powered by Google's Gemini AI.

## Key Features
- Real-time game tracking with timestamped play-by-play updates
- AI-powered voice assistant for baseball queries
- Interactive UI with animated transitions
- Live score updates
- Chronological game summaries

## Test Instruction
1. Launch mlb_data to gain the recent mlb datas from api and saved to json files.
2. Launch the server and subsitute to your own google cloud credentials and project name.
3. Open the mlb2.xcodeproj/project.pbxproj file to launch the pocketball application. 

### Backend Components

#### 1. server.py
The FastAPI server that handles:
- Live game data processing
- Game summaries
- MLB historical data access
- Voice transcription and response generation

necessary JSON files:
- `info.json`: MLB historical data
- `liveData.json`: Automatically create by mlb_data.py file

#### 2. mlb_data.py
Handles MLB data fetching and processing:
- Retrieves live game data from MLB API
- Processes play-by-play information
- Saves formatted data to JSON files

Key functions:
def get_current_play_info(game_id) # Fetches live game data
def save_live_data(play_info_list) # Saves to JSON
def print_play_info(play_info_list) # Debug output
