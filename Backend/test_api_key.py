#!/usr/bin/env python3
"""
Test script to validate the Google Gemini API key
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ GOOGLE_API_KEY not found in .env file")
    exit(1)

print(f"Testing API Key: {api_key[:20]}...")
print(f"Full key length: {len(api_key)}")

# Try using the google-generativeai library
try:
    import google.generativeai as genai
    
    print("\n[1] Configuring Gemini API...")
    genai.configure(api_key=api_key)
    
    print("[2] Creating model instance...")
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    print("[3] Sending test request...")
    response = model.generate_content("Say 'API key is valid' in one sentence")
    
    print(f"✅ SUCCESS! Response: {response.text[:100]}")
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}")
    print(f"Message: {e}")
    
    # Try to get more details
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
