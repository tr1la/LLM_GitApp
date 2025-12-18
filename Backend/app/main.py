import base64
import cv2
from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fpdf import FPDF
import numpy as np
import openai
from pydantic import BaseModel, Json
from sympy import content

import time

# Preload Whisper model for better performance
whisper_model = None
whisper_model_timestamp = 0
whisper_model_loading = False  # Flag to prevent concurrent loading
WHISPER_MODEL_CACHE_DURATION = 3600  # Cache for 1 hour

def load_whisper_model():
    global whisper_model, whisper_model_timestamp, whisper_model_loading
    
    # Prevent concurrent loading
    if whisper_model_loading:
        print("⏳ Whisper model is already loading, waiting...")
        # Wait until loading is complete (simple approach)
        while whisper_model_loading:
            time.sleep(0.1)
        return whisper_model
    
    # Check if model needs to be refreshed (cache invalidation)
    current_time = time.time()
    if whisper_model is not None and (current_time - whisper_model_timestamp) < WHISPER_MODEL_CACHE_DURATION:
        print("⚡ Using cached Whisper model")
        return whisper_model
    
    # Load or reload the model
    try:
        whisper_model_loading = True
        import whisper
        print("🔄 Loading Whisper model...")
        whisper_model = whisper.load_model("base.en")
        whisper_model_timestamp = time.time()
        print("✅ Whisper model loaded successfully")
    except Exception as e:
        print(f"⚠️  Failed to load Whisper model: {e}")
        whisper_model = None
    finally:
        whisper_model_loading = False
    return whisper_model

# Load model on startup
load_whisper_model()

from app.article_reading.pipeline import execute_pipeline
from app.question_answering.pipeline import ask_general_question
from app.utils.audio import FEATURE_KEYWORDS_FOR_SEMANTIC_MATCH, FEATURE_LABELS, FEATURE_NAMES, find_navigation_intent, route_query_semantically
from app.utils.deepgram import transcribe_audio
from .utils.formatter import create_pdf, create_pdf_async, format_article_audio_response, format_audio_response
from .config import config
from .text_recognition.provider.ocr.ocr import OcrRecognition
import sys
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile
from deepface import DeepFace
import time
import asyncio
import json
import mimetypes
from fastapi import FastAPI, UploadFile, File
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
from pathlib import Path
import os
import tempfile
import requests
from collections import OrderedDict
from .all_task.pipeline import get_llm_response
import urllib.parse

# Initialize the sentence transformer model
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Load .env from the project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize NLTK data for article processing
from .utils.nltk_init import download_nltk_data
download_nltk_data()

start = time.time()
# ocr = OcrRecognition()
# currency_detection_model_path = "./models/best8.onnx"
# currency_detector = YOLOv8(currency_detection_model_path, conf_thres=0.2, iou_thres=0.3)
# barcode_processor = BarcodeProcessor()
# distance_estimation_model_path = "./models/yolov8m.onnx"


app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define allowed origins (frontend URLs)

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/health")
async def health_check():
    global whisper_model, whisper_model_timestamp
    
    # Check Whisper model status
    model_status = "loaded" if whisper_model is not None else "not loaded"
    
    # Calculate model age if loaded
    model_age = 0
    if whisper_model is not None:
        import time
        model_age = time.time() - whisper_model_timestamp
    
    return {
        "status": "healthy",
        "whisper_model": {
            "status": model_status,
            "age_seconds": model_age
        }
    }

@app.post("/document_recognition")
async def document_recognition(file: UploadFile = File(...)):
    try:
        start = time.time()
        image_data = await file.read()
        base64_image = base64.b64encode(image_data).decode("utf-8")

        result = get_llm_response(
            query="Extract text from this image.",
            task="text_recognition",
            base64_image=base64_image,
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to generate text response")

        return JSONResponse(content={
            "status": "success",
            "text": result,
        })

    except Exception as e:
        print(f"Lỗi xảy ra: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


image_path = "./app/dis.jpg"  


@app.post("music_detection")
async def music_detection(file: UploadFile = File(...)):
    try:
        with NamedTemporaryFile(delete=False) as temp:
            temp.write(file.file.read())
            temp_path = temp.name

        audio_path = format_audio_response(temp_path, "music_recognition")
        if audio_path:
            return JSONResponse(content={
                "audio_path": audio_path,
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to generate audio response")

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")


# --- Modified API Endpoint ---
# @app.post("/transcribe_audio_v2")
async def process_voice_command(file: UploadFile = File(...), current_feature: str | None = None):
    """
    Processes voice input, distinguishing navigation commands from feature queries.

    Args:
        file: The uploaded audio file (.webm format expected).
        current_feature: The key/name of the feature currently active in the UI (optional).
                         Helps disambiguate queries. e.g., "News", "Text".

    Returns:
        A dictionary containing the transcription, recognized intent ('navigate' or 'query'),
        target feature, confidence score, and original query text if applicable.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        transcript_result = transcribe_audio(tmp_path)

        if not transcript_result or "transcript" not in transcript_result:
             raise HTTPException(status_code=500, detail="Transcription failed.")

        transcript_text = transcript_result.get("transcript", "").strip()

        if not transcript_text:
             raise HTTPException(status_code=400, detail="Empty transcript received.")

        # --- STAGE 1: Check for Navigation Intent ---
        navigation_result = find_navigation_intent(transcript_text)

        if navigation_result:
            # It's a command to navigate!
            return {
                "transcript": transcript_result,
                "intent": navigation_result["intent"],
                "command": navigation_result["target_feature"],
                "confidence": navigation_result["confidence"],
                "query": None # Not a query
            }

        # --- STAGE 2: Treat as Query (if not navigation) ---
        # Option A: If context is known, assume query is for the current feature
        if current_feature and current_feature in FEATURE_NAMES: # Check if valid feature key
             # Simple Action Keywords check within current context (e.g., "stop", "play")
             # These might override semantic routing if they are very clear actions
             if transcript_text.lower() == "stop":
                  return {
                       "transcript": transcript_result,
                       "intent": "action", # Could be a specific 'action' intent
                       "target_feature": current_feature, # Action applies to current feature
                       "command": "Stop", # Specific action identified
                       "confidence": 0.99,
                       "query": transcript_text
                  }
             if transcript_text.lower() == "play":
                   return {
                       "transcript": transcript_result,
                       "intent": "action",
                       "target_feature": current_feature,
                       "command": "Play",
                       "confidence": 0.99,
                       "query": transcript_text
                  }

             # Otherwise, it's a query for the current feature
             return {
                "transcript": transcript_result,
                "intent": "query",
                "command": current_feature, # Route to the active feature
                "confidence": 0.90, # High confidence because context is provided
                "query": transcript_text
             }

        # Option B: Context unknown or it's a query needing routing
        # Use semantic similarity to find the best feature *for the query*
        semantic_routing_result = route_query_semantically(
            transcript_text,
            embedder,
            FEATURE_KEYWORDS_FOR_SEMANTIC_MATCH # Use the detailed keywords here
        )

        return {
            "transcript": transcript_result,
            "intent": semantic_routing_result["intent"],
            "command": semantic_routing_result["target_feature"],
            "confidence": semantic_routing_result["confidence"],
            "query": semantic_routing_result["query"]
        }

    except Exception as e:
        print(f"❌ Error processing voice command: {e}")
        # Log the exception traceback for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process audio: {str(e)}")
    finally:
        # Clean up the temporary file
        import os
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
             os.unlink(tmp_path)

from typing import Annotated


@app.post("/transcribe_audio")
async def voice_command(
    file: Annotated[UploadFile, File()],
    current_feature: Annotated[str, Form()]
    ):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        transcript_result = transcribe_audio(tmp_path)
        transcript_text = transcript_result.get("transcript", "").lower()

        print("Transcript:", transcript_text)
        print("Current Feature:", current_feature)

        # Step 1: Exact keyword match
        for label, keywords in FEATURE_LABELS.items():
            for keyword in keywords:
                if keyword.lower() in transcript_text:
                    if label == current_feature:
                        if "read" not in transcript_text.lower():
                            return {
                                "command": current_feature,
                                "intent": "query",
                                "confidence": 0.9,  # high confidence
                                "query": transcript_text
                            }
                        else:
                            return {
                                "command": current_feature,
                                "intent": "read",
                                "confidence": 0.9,  # high confidence
                                "query": transcript_text
                            }
                        
                    return {
                        "command": label,
                        "intent": "navigate",
                        "confidence": 1.0,  # exact match = high confidence
                        "query": transcript_text
                    }

        # Step 2: Semantic similarity fallback
        transcript_embed = embedder.encode(transcript_text, convert_to_tensor=True)
        best_match, best_score = None, -1

        for label, phrases in FEATURE_LABELS.items():
            for phrase in phrases:
                phrase_embed = embedder.encode(phrase, convert_to_tensor=True)
                score = util.cos_sim(transcript_embed, phrase_embed).item()
                if score > best_score:
                    best_match, best_score = label, score

        return {
            "command": best_match,
            "intent": "navigate",
            "confidence": round(best_score, 3),
            "query": transcript_text
        }
    except Exception as e:
        print("❌ Error:", e)
        return {"error": "Failed to process audio."}


class NewsQuery(BaseModel):
    news_query: str

class ChatbotQuery(BaseModel):
    message: str

@app.post("/fetching_news")
async def article_reading(news_query: str = Form(...)):

    try:
        if not news_query:
            raise HTTPException(status_code=400, detail="No news query provided")       

        # process audio to extract the news query
        if "error" in news_query:
            raise HTTPException(status_code=400, detail="Failed to transcribe audio")
        
        articles = execute_pipeline(news_query)

        if not articles:
            raise HTTPException(status_code=400, detail="No valid articles found")
        
        res = []

        for i, article in enumerate(articles):
            res.append({
                "title": article.title,
                "text": article.text,
                "summary": article.summary,
                "url": article.url
            })
        

        return JSONResponse(content={
            "articles": res,
            
        },
        status_code=200)  # Explicitly return 200 OK)
    except Exception as e:
        print(e)
        return {"error": "Failed to process audio."}

@app.post("/general_question_answering")
async def general_qa(message: str = Form(...)):

    try:
        print(f"[DEBUG] Received message: {message}", flush=True)

        # Step 3: Ask the LLM to answer the question
        answer = get_llm_response(
            query=message,
            task="general_question_answering",
            base64_image=None
        )
        print(f"[DEBUG] LLM Response: {answer}", flush=True)

        # Step 4: Convert answer back to speech
        #audio_path = format_audio_response(answer, "general_question_answering")
        #print(f"[DEBUG] Audio path: {audio_path}", flush=True)
        return JSONResponse(content={
                "reply": answer,
            }, status_code=200) 
        if audio_path:
            print(f"[DEBUG] Returning 200 OK with reply: {answer}", flush=True)
            return JSONResponse(content={
                "reply": answer,
            }, status_code=200)  # Explicitly return 200 OK
        else:
            print(f"[DEBUG] Audio generation failed", flush=True)
            # Still return the text response even if audio generation fails
            return JSONResponse(content={
                "reply": answer,
            }, status_code=200)

    except Exception as e:
        print(f"[ERROR] Exception: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/download_pdf")
async def download_pdf(pdf_path: str):
    return FileResponse(pdf_path, media_type="application/pdf", filename="document.pdf")


@app.get("/download_audio")
async def download_audio(audio_path: str):
    return FileResponse(audio_path, media_type="audio/mpeg", filename="document.mp3")


# Spotify Authentication Routes
@app.get("/spotify/login")
async def spotify_login():
    """Redirect user to Spotify authorization page"""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:3000/spotify-callback")
    
    # Required scopes for the Spotify Web API
    scopes = [
        "streaming",
        "user-read-email",
        "user-read-private",
        "user-modify-playback-state",
        "user-read-playback-state",
        "user-read-currently-playing",
        "app-remote-control"
    ]
    
    scope = " ".join(scopes)
    
    # Build authorization URL
    auth_url = (
        "https://accounts.spotify.com/authorize?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
        f"scope={urllib.parse.quote(scope)}"
    )
    
    return JSONResponse(content={"auth_url": auth_url})

@app.get("/spotify/callback")
async def spotify_callback(code: str):
    """Handle Spotify callback and exchange code for tokens"""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:3000/spotify-callback")
    
    # Exchange authorization code for access token
    token_url = "https://accounts.spotify.com/api/token"
    
    # Prepare the request body
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    
    # Prepare the authorization header
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    # Make the request
    response = requests.post(
        token_url,
        data=data,
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    if response.status_code != 200:
        error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
        error_description = error_data.get('error_description', 'Failed to get access token from Spotify')
        # Return error as JSON instead of redirecting
        return JSONResponse(content={"error": error_description}, status_code=400)
    
    token_data = response.json()
    
    # Return tokens in response body instead of redirecting
    return JSONResponse(content={
        "access_token": token_data.get('access_token', ''),
        "refresh_token": token_data.get('refresh_token', ''),
        "expires_in": token_data.get('expires_in', ''),
        "token_type": token_data.get('token_type', '')
    })


@app.post("/spotify/refresh")
async def spotify_refresh_token(request: Request):
    """Refresh Spotify access token"""
    try:
        # Get refresh token from request body
        body = await request.json()
        refresh_token = body.get("refresh_token")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request body")
    
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token is required")
    
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    # Exchange refresh token for new access token
    token_url = "https://accounts.spotify.com/api/token"
    
    # Prepare the request body
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    
    # Prepare the authorization header
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    # Make the request
    response = requests.post(
        token_url,
        data=data,
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to refresh access token")
    
    token_data = response.json()
    
    # Return new access token
    return JSONResponse(content={
        "access_token": token_data.get("access_token"),
        "expires_in": token_data.get("expires_in"),
        "token_type": token_data.get("token_type")
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=config.HOST, port=int(config.PORT), reload=True)
