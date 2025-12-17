from ..config import config
import os
import tempfile
from typing import Dict, Any

# Try to import whisper, but don't fail if it's not available
try:
    import whisper
    # Use the preloaded model from main.py
    from ..main import whisper_model
    model = whisper_model
except ImportError:
    whisper = None
    model = None

import time

def transcribe_audio(audio_file_path):
    # Check if whisper is available
    if whisper is None or model is None:
        print("❌ Whisper model not available")
        return {"error": "Whisper model not available. Please install openai-whisper."}
    
    start_time = time.time()
    try:
        # Check if the audio file exists
        if not os.path.exists(audio_file_path):
            print("❌ Audio file not found:", audio_file_path)
            return {"error": "Audio file not found."}

        # Check if the file is a valid audio file
        if not audio_file_path.endswith(('.wav', '.mp3', '.webm', '.m4a', '.mp4', '.mpeg', '.mpga', '.ogg', '.flac')):
            print("❌ Invalid audio file format:", audio_file_path)
            return {"error": "Invalid audio file format."}

        print("🔄 Starting transcription with Whisper model...")
        # Transcribe audio file using local Whisper model
        result = model.transcribe(audio_file_path)
        transcript = result["text"].strip()
        
        # Calculate transcription time
        end_time = time.time()
        duration = end_time - start_time
        print(f"⏱️  Transcription completed in {duration:.2f} seconds")
        print("🎙️ Transcript:", transcript)

        if not transcript:
            return {"error": "No transcript detected."}
        
        return {"transcript": transcript}

    except Exception as e:
        print("❌ Exception:", str(e))
        import traceback
        traceback.print_exc()
        return {"error": f"An error occurred during transcription: {str(e)}"}