"""
MIT License

Copyright (c) 2024 [Xinpeng Shou]

See LICENSE file for the complete license terms.
"""

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from google.cloud import speech, texttospeech
import os
import uvicorn
import logging
import vertexai
from vertexai.preview.generative_models import GenerativeModel, SafetySetting, Part, Tool
from vertexai.preview.generative_models import grounding
import base64
import json
from fastapi import Request

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "Your-Credentials"

# Initialize the Speech client
client = speech.SpeechClient()

# Initialize the Text-to-Speech client
tts_client = texttospeech.TextToSpeechClient()

# Initialize Vertex AI and Gemini
vertexai.init(project="Your-Project-Name", location="us-central1")


def initialize_gemini():
    textsi_1 = """You are a friendly baseball expert. Your name is Pocketball. Your role is to:
    1. Always respond about baseball and Major League Baseball topics only
    2. Keep responses fun and engaging
    3. Limit responses to exactly two sentences
    4. Never break character as an MLB expert
    5. If asked about non-baseball topics, politely redirect to baseball
    
    If user asks: Hey PocketBall, what's the score of the Yankees vs. Dogers last game?
    answer: The Dogers won 7-6 against the Yankees, with Mookie Betts hitting a game-winning homer in the 8th!
    """

    model = GenerativeModel(
        "gemini-1.5-flash-002",
        system_instruction=[textsi_1],
        generation_config={
            "max_output_tokens": 1054,
            "temperature": 1,
            "top_p": 0.95,
        },
        safety_settings=[
            SafetySetting(
                category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=SafetySetting.HarmBlockThreshold.OFF
            ),
            SafetySetting(
                category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=SafetySetting.HarmBlockThreshold.OFF
            ),
            SafetySetting(
                category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=SafetySetting.HarmBlockThreshold.OFF
            ),
            SafetySetting(
                category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=SafetySetting.HarmBlockThreshold.OFF
            ),
        ]
    )

    return model.start_chat(history=[], response_validation=False)


# Initialize Gemini chat
chat = initialize_gemini()


async def get_gemini_response(transcription: str, max_retries: int = 3) -> str:
    """Get response from Gemini with retry logic."""
    for attempt in range(max_retries):
        try:
            gemini_response = chat.send_message(transcription)
            return gemini_response.text
        except Exception as e:
            logger.error(f"❌ Gemini attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                return "I apologize, but I'm having trouble responding right now. Please try again."
    return "I apologize, but I'm having trouble responding right now. Please try again."


@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    logger.info("🎤 Received audio file: %s", file.filename)

    try:
        # Read the uploaded file content
        content = await file.read()
        logger.info("📁 File size: %d bytes", len(content))

        # Create the audio object
        audio = speech.RecognitionAudio(content=content)

        # Configure the recognition settings
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=44100,
            language_code="en-US",
            enable_automatic_punctuation=True,
        )

        # Perform the transcription
        logger.info("🎯 Starting transcription...")
        response = client.recognize(config=config, audio=audio)

        # Process the results
        transcription = ""
        for result in response.results:
            transcription += result.alternatives[0].transcript
            confidence = result.alternatives[0].confidence
            logger.info("🗣️ Transcribed: %s", transcription)
            logger.info("📊 Confidence: %.2f", confidence)

        # Get Gemini's response
        if transcription:
            logger.info("\n" + "=" * 50)
            logger.info("💬 User said: %s", transcription)
            logger.info("🤖 Asking Gemini...")

            gemini_text = await get_gemini_response(transcription)

            # Convert Gemini's response to speech
            audio_content = text_to_speech(gemini_text)

            logger.info("\n🤖 Gemini's response:")
            logger.info("-" * 50)
            logger.info(gemini_text)
            logger.info("=" * 50 + "\n")

            return {
                "text": transcription,
                "gemini_response": gemini_text,
                "audio_content": base64.b64encode(audio_content).decode('utf-8')
            }

        return {"text": transcription}

    except Exception as e:
        logger.error("❌ Error during processing: %s", str(e))
        return {"error": str(e)}


def text_to_speech(text: str) -> bytes:
    """Convert text to speech using Google Cloud Text-to-Speech API."""
    logger.info("🔊 Converting text to speech...")

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Casual-K",
        ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    try:
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        logger.info("✅ Text-to-speech conversion successful")
        return response.audio_content
    except Exception as e:
        logger.error("❌ Error in text-to-speech conversion: %s", str(e))
        raise


@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy"}


# Initialize two different Gemini instances
regular_chat = initialize_gemini()  # For ContentView


def initialize_rag_gemini():
    textsi_2 = """You are an MLB historian expert. Your role is to:
    1. Use the provided MLB historical information to give accurate responses
    2. Keep responses engaging and informative
    3. Limit responses to exactly two sentences
    4. Focus on MLB history, stats, and memorable moments
    5. If information is not in the context, use your general knowledge"""

    model = GenerativeModel(
        "gemini-1.5-pro",
        generation_config={
            "max_output_tokens": 1054,
            "temperature": 0.9,
        }
    )
    return model


rag_model = initialize_rag_gemini()  # For LogoView


# Add the new endpoint for MLB history
@app.post("/mlb_history/")
async def mlb_history(request: Request):
    try:
        data = await request.json()
        query = data.get("query", "")

        # Load MLB info from JSON file
        with open("info.json", "r") as f:
            mlb_info = json.load(f)

        # Create context-aware prompt
        prompt = f"""
        MLB Historical Context:
        {json.dumps(mlb_info, indent=2)}

        User Question: {query}

        Please provide a response using the above MLB historical information. Keep it to two sentences.
        """

        response = rag_model.generate_content(prompt)
        return {"response": response.text}

    except Exception as e:
        logger.error(f"❌ MLB History error: {str(e)}")
        return {"response": "I apologize, but I'm having trouble accessing MLB history right now. Please try again."}


@app.get("/live_games/")
async def get_live_games():
    try:
        with open("info.json", "r") as f:
            data = json.load(f)

        # Check for live games in the data
        if data.get("dates"):
            today_games = data["dates"][0]["games"]
            live_games = [game for game in today_games
                          if game["status"]["abstractGameState"] == "Live"]

            if live_games:
                game = live_games[0]  # Get first live game
                away_team = game["teams"]["away"]["team"]["name"]
                home_team = game["teams"]["home"]["team"]["name"]
                away_score = game["teams"]["away"]["score"]
                home_score = game["teams"]["home"]["score"]

                game_info = f"LIVE: {away_team} ({away_score}) vs {home_team} ({home_score})"
                return {"game_info": game_info}

        return {"game_info": "No live games at the moment"}

    except Exception as e:
        logger.error(f"Error getting live games: {str(e)}")
        return {"game_info": "Unable to fetch game information"}


@app.get("/game_summary/")
async def get_game_summary():
    try:
        # Read the live game data
        with open("liveData.json", "r") as f:
            data = json.load(f)

        all_plays = data['liveData']['plays']['allPlays']

        # Sort plays by startTime
        sorted_plays = sorted(all_plays, key=lambda x: x['about']['startTime'])

        # Generate summary
        summary = []
        for play in sorted_plays:
            # Format timestamp
            timestamp = play['about']['startTime'].replace('T', ' ').replace('Z', '')
            inning = play['about']['inning']
            is_top = "Top" if play['about']['isTopInning'] else "Bottom"
            description = play['result']['description']
            away_score = play['result']['awayScore']
            home_score = play['result']['homeScore']

            # Format the play summary with timestamp on its own line
            play_summary = f"{timestamp}\n{is_top} {inning}: {description} (Score: {away_score}-{home_score})\n"
            summary.append(play_summary)

        # Join all summaries with line breaks
        full_summary = "\n".join(summary)
        return {"summary": full_summary}

    except Exception as e:
        logger.error(f"Error generating game summary: {str(e)}")
        return {"summary": "Unable to generate game summary"}


if __name__ == "__main__":
    logger.info("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
